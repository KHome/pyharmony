"""Client class for connecting to the Logitech Harmony."""

import json
import logging
import time

import sleekxmpp
from sleekxmpp.xmlstream import ET
from pyharmony import auth as harmony_auth


LOGGER = logging.getLogger(__name__)


class HarmonyClient(sleekxmpp.ClientXMPP):
    """An XMPP client for connecting to the Logitech Harmony."""

    def __init__(self, email, passwd, harmony_ip, harmony_port=None):
        self.port = harmony_port or '5222'
        self.email = email
        self.passwd = passwd
        self.ip_address = harmony_ip
        self.token = harmony_auth.get_auth_token(self.ip_address, self.port)

        user = '%s@connect.logitech.com/gatorade.' % self.token
        password = self.token
        plugin_config = {
            # Enables PLAIN authentication which is off by default.
            'feature_mechanisms': {'unencrypted_plain': True},
        }
        super(HarmonyClient, self).__init__(
            user, password, plugin_config=plugin_config)
        self.connect(address=(self.ip_address, self.port),
                       use_tls=False, use_ssl=False)
        self.process(block=False)

        while not self.sessionstarted:
            time.sleep(0.1)

    def login_to_logitech_site(self):
        token = auth.login(self.email, self.passwd)
        if not token:
            print('Could not get token from  Logitech server.')
            return None

        session_token = auth.swap_auth_token(
            self.ip_address, self.port, token)
        if not session_token:
            print('Could not swap login token for session token.')
            return None

        return session_token

    def get_config(self):
        """Retrieves the Harmony device configuration.

        Returns:
          A nested dictionary containing activities, devices, etc.
        """
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = (
            'vnd.logitech.harmony/vnd.logitech.harmony.engine?config')
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=True)
        payload = result.get_payload()
        assert len(payload) == 1
        action_cmd = payload[0]
        assert action_cmd.attrib['errorcode'] == '200'
        device_list = action_cmd.text
        return json.loads(device_list)

    def get_current_activity(self):
        """Retrieves the current activity.

        Returns:
          A int with the activity ID.
        """
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = (
            'vnd.logitech.harmony/vnd.logitech.harmony.engine?getCurrentActivity')
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=True)
        payload = result.get_payload()
        assert len(payload) == 1
        action_cmd = payload[0]
        assert action_cmd.attrib['errorcode'] == '200'
        activity = action_cmd.text.split("=")
        return int(activity[1])

    def _timestamp(self):
        return str(int(round(time.time() * 1000)))

    def start_activity(self, activity_id):
        """Starts an activity.

        Args:
            activity_id: An int or string identifying the activity to start
        """
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = ('harmony.activityengine?runactivity')
        cmd = 'activityId=' + str(activity_id) + ':timestamp=' + self._timestamp() + ':async=1'
        action_cmd.text = cmd
        iq_cmd.set_payload(action_cmd)
        iq_cmd.send(block=True)
        return True

    def sync(self):
        """Syncs the harmony hub with the web service."""

        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = ('setup.sync')
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=True)
        payload = result.get_payload()
        assert len(payload) == 1

    def send_command(self, device_id, command):
        """Send a simple command to the Harmony Hub."""

        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        iq_cmd['id'] = '5e518d07-bcc2-4634-ba3d-c20f338d8927-2'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = (
            'vnd.logitech.harmony/vnd.logitech.harmony.engine?holdAction')
        action_cmd.text = 'action={"type"::"IRCommand","deviceId"::"'+str(device_id)+'","command"::"'+command+'"}:status=press'
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=False)

        action_cmd.attrib['mime'] = (
            'vnd.logitech.harmony/vnd.logitech.harmony.engine?holdAction')
        action_cmd.text = 'action={"type"::"IRCommand","deviceId"::"'+device_id+'","command"::"'+command+'"}:status=release'
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=False)

        return result

    def turn_off(self):
        """Turns the system off if it's on, otherwise it does nothing.

        Returns:
          True.
        """
        activity = self.get_current_activity()
        print(activity)
        if activity != -1:
            print("OFF")
            self.start_activity(-1)
        return True
