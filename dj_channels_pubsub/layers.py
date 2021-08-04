import asyncio
import functools
import os
import random
import string
import time
import uuid

from channels.exceptions import ChannelFull
from channels.layers import BaseChannelLayer

from google.cloud import pubsub
from .utils import SetQueue


class GcePubSubChannelLayer(BaseChannelLayer):
    """
    Google cloud Pub/Sub channel layer implementation
    """

    def __init__(
        self,
        expiry=60,
        group_expiry=86400,
        capacity=100,
        channel_capacity=None,
        **kwargs
    ):
        super().__init__(
            expiry=expiry,
            capacity=capacity,
            channel_capacity=channel_capacity,
            **kwargs
        )
        self.project = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.channels = {}
        self.groups = {}
        self.group_expiry = group_expiry
        self._publisher_client = None
        self._subscriber_client = None
        self._subscribes = {}
        self._messages = {}
        self.queue_limit = 1000

    # Channel layer API
    extensions = ["groups", "flush"]

    @property
    def publisher_client(self):
        if self._publisher_client is None:
            self._publisher_client = pubsub.PublisherClient()
        return self._publisher_client

    @property
    def subscriber_client(self):
        if self._subscriber_client is None:
            self._subscriber_client = pubsub.SubscriberClient()
        return self._subscriber_client

    async def send(self, channel, message):
        """
        Send a message onto a (general or specific) channel.
        """
        # Typecheck
        assert isinstance(message, dict), "message is not a dict"
        assert self.valid_channel_name(channel), "Channel name not valid"
        # If it's a process-local channel, strip off local part and stick full
        # name in message
        assert "__asgi_channel__" not in message

        if channel in self.channels:
            topic_name = self.channels.get(channel)
        else:
            topic_name = 'projects/{project_id}/topics/{topic}'.format(
                project_id=self.project,
                topic=channel,  # Set this to something appropriate.
            )
            self.publisher_client.create_topic(name=topic_name)
            self.channels[channel] = topic_name
        future = self.publisher_client.publish(topic_name, b'', **message)
        future.result()

    async def receive(self, channel):
        """
        Receive the first message that arrives on the channel.
        If more than one coroutine waits on the same channel, a random one
        of the waiting coroutines will get the result.
        """
        assert self.valid_channel_name(channel)

        if channel in self._subscribes:
            subscription_path = self._subscribes[channel]
        else:
            if channel in self.channels:
                topic_name = self.channels.get(channel)
            else:
                topic_name = 'projects/{project_id}/topics/{topic}'.format(
                    project_id=self.project,
                    topic=channel,  # Set this to something appropriate.
                )
                self.publisher_client.create_topic(name=topic_name)
                self.channels[channel] = topic_name
            sub = await self.generate_sub_name(channel)
            subscription_path = self.subscriber_client.subscription_path(self.project, sub)
            self._subscribes[channel] = subscription_path
            self.subscriber_client.create_subscription(request={"name": subscription_path, "topic": topic_name})
            self.subscriber_client.subscribe(subscription_path, functools.partial(self._receive_callback, channel))

        while channel not in self._messages:
            await asyncio.sleep(1)
        while self._messages[channel].empty():
            await asyncio.sleep(0.1)

        message = self._messages[channel].get()
        message.ack()
        return message.attributes

    def _receive_callback(self, channel, message):
        if channel not in self._messages:
            self._messages[channel] = SetQueue(maxsize=self.queue_limit)
        self._messages[channel].put(message)

    async def generate_sub_name(self, channel):
        """
        Returns a new subsciption name that can be used by sub client for this client specifically
        """
        return "%s.gce_sub.%s" % (
            channel,
            uuid.uuid4(),
        )

    async def new_channel(self, prefix="specific."):
        """
        Returns a new channel name that can be used by something in our
        process as a specific channel.
        """
        return "%s.gce_pubsub_channel.%s" % (
            prefix,
            "".join(random.choice(string.ascii_letters) for i in range(12)),
        )

    # Expire cleanup
    def _clean_expired(self):
        """
        Goes through all messages and groups and removes those that are expired.
        Any channel with an expired message is removed from all groups.
        """
        # Group Expiration
        timeout = int(time.time()) - self.group_expiry
        for group in self.groups:
            for channel in list(self.groups.get(group, set())):
                # If join time is older than group_expiry end the group membership
                if (
                    self.groups[group][channel]
                    and int(self.groups[group][channel]) < timeout
                ):
                    # Delete from group
                    del self.groups[group][channel]

    # Flush extension
    async def flush(self):
        self.channels = {}
        self.groups = {}
        self._messages = {}
        for sub_path in self._subscribes:
            self.subscriber_client.delete_subscription(request={"subscription": sub_path})

    async def close(self):
        # Nothing to go
        pass

    def _remove_from_groups(self, channel):
        """
        Removes a channel from all groups. Used when a message on it expires.
        """
        for channels in self.groups.values():
            if channel in channels:
                del channels[channel]

    # Groups extension
    async def group_add(self, group, channel):
        """
        Adds the channel name to a group.
        """
        # Check the inputs
        assert self.valid_group_name(group), "Group name not valid"
        assert self.valid_channel_name(channel), "Channel name not valid"
        # Add to group dict
        self.groups.setdefault(group, {})
        self.groups[group][channel] = time.time()

    async def group_discard(self, group, channel):
        # Both should be text and valid
        assert self.valid_channel_name(channel), "Invalid channel name"
        assert self.valid_group_name(group), "Invalid group name"
        # Remove from group set
        if group in self.groups:
            if channel in self.groups[group]:
                del self.groups[group][channel]
            if not self.groups[group]:
                del self.groups[group]

    async def group_send(self, group, message):
        # Check types
        assert isinstance(message, dict), "Message is not a dict"
        assert self.valid_group_name(group), "Invalid group name"
        # Run clean
        self._clean_expired()
        # Send to each channel
        for channel in self.groups.get(group, set()):
            try:
                await self.send(channel, message)
            except ChannelFull:
                pass
