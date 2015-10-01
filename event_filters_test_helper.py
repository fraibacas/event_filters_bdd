"""
"""
from utils.event_injector import EventInjector
from utils.zenoss_client import ZenossClient

import json
import time

FIELD_NAME_TO_FILED_ID = {
		"Count" : "count",
		"Last Seen" : "lastTime",
		"First Seen" : "firstTime",
		"Summary" : "summary",
		"Event Class" : "eventClass",
		"Component" : "component",
		"Resource" : "device",
		"Status" : "eventState",
		"Severity" : "severity",
		"Event State" : "eventState",
		"Device Class" : "DeviceClass",
		"Owner" : "ownerid",
		"Agent" : "agent",
		"Collector" : "monitor",
		"Event Key" : "eventKey",
		"Event Class Key" : "eventClassKey",
		"Event Group" : "eventGroup",
		"Device Priority" : "DevicePriority",
		"Event Class Mapping" : "eventClassMapping",
		"Event ID" : "evid",
		"Fingerprint" : "dedupid",
		"Groups" : "DeviceGroups",
		"IP Address" : "ipAddress",
		"Location" : "Location",
		"Message" : "message",
		"Production State" : "prodState",
		"State Change" : "stateChange",
		"Systems" : "Systems",
	}

class EventFiltersTestHelper(object):

	def __init__(self):
		self.config = {}
		self.zenoss_client = ZenossClient()
		self.event_injector = EventInjector()

	def init(self):
		""" """
		with open("./config.json") as json_file:
			self.config = json.load(json_file)
			self.event_injector.init(self.config)
			self.zenoss_client.init(self.config)

	def shutdown(self):
		self.zenoss_client.shutdown()
		self.event_injector.shutdown()

	def load_sample_events(self):
		""" """
		events = []
		with open("./features/events.json") as json_file:
			json_events = json.load(json_file)
			events = json_events["events"]
		return events

	def create_event(self, event, archive):
		return self.event_injector.inject_event(event, archive)

	def delete_event(self, uuid, archive):
		self.event_injector.delete_event(uuid, archive)

	def are_uuids_indexed(self, uuids, archive):
		event_ids = [ "{0}".format(uuid) for uuid in uuids ]
		data = self.zenoss_client.send_event_filter_request({'evid': event_ids}, archive)
		return data['totalCount'] == len(event_ids)

	def is_zep_router_available(self):
		response = self.zenoss_client.send_event_filter_request()
		return response.get('success')

	def send_event_filter_request(self, event_filter, archive, sort = {}):
		""" """
		request_info = {}
		params = {}
		for field, field_filter in event_filter.iteritems():
			field_id = FIELD_NAME_TO_FILED_ID[field]
			params[field_id] = field_filter
		request_info["params"] = params
		request_info["keys"] = ['evid']
		if sort:
			request_info["sort"] = FIELD_NAME_TO_FILED_ID[sort['sort']]
			request_info["dir"] = sort['dir']
		response = self.zenoss_client.send_event_filter_request(request_info, archive)
		return response

	def get_uuids_from_response(self, zep_reponse):
		uuids = []
		if zep_reponse.get('events'):
			for event in zep_reponse.get('events'):
				uuids.append(event['evid'])
		return uuids
