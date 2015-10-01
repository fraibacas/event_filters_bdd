"""
Class to inject events in the database. Use caution
"""

import json
import time
import uuid
import pymysql

class EventInjector(object):
	"""
	Injects events in event database 
	"""

	field_name_to_id_mapping = {
		"Summary": 			"summary",
		"Resource": 		"element_identifier",
		"Component": 		"element_sub_identifier",
		"Count": 			"event_count",
		"First Seen": 		"first_seen",
		"Last Seen": 		"last_seen",
		"Agent": 			"agent_id",
		"Collector": 		"monitor_id",
		"Device Class": 	"zenoss.device.device_class",
		"Device Priority": 	"zenoss.device.priority",
		"Event Class":     	"event_class_id",
		"Event Class Key": 	"event_class_key_id",
		"Event Group": 		"event_group_id",
		"Event ID":   		"uuid",
		"Event Key": 		"event_key_id",
		"Fingerprint": 		"fingerprint",
		"Groups": 			"zenoss.device.groups",
		"IP Address": 		"zenoss.device.ip_address",
		"Location": 		"zenoss.device.location",
		"Message": 			"message",
		"Owner": 			"current_user_name",
		"Production State": "zenoss.device.production_state",
		"Severity": 		"severity_id",
		"State Change": 	"status_change",
		"Status": 			"status_id",
		"Systems": 			"zenoss.device.systems",
	}


	field_name_translator = {
		"summary": 						"Summary",
		"element_identifier": 			"Resource",
		"element_sub_identifier": 		"Component",
		"event_count": 					"Count",
		"first_seen": 					"First Seen",
		"last_seen": 					"Last Seen",
		"agent_id": 					"Agent",
		"monitor_id": 					"Collector",
		"zenoss.device.device_class": 	"Device Class",
		"zenoss.device.priority": 		"Device Priority",
		"event_class_id": 				"Event Class",
		"event_class_key_id": 			"Event Class Key",
		"event_group_id": 				"Event Group",
		"uuid": 						"Event ID",
		"event_key_id": 			    "Event Key",
		"fingerprint": 					"Fingerprint",
		"zenoss.device.groups": 		"Groups",
		"zenoss.device.ip_address": 	"IP Address",
		"zenoss.device.location": 		"Location",
		"message": 						"Message",
		"current_user_name": 			"Owner",
		"zenoss.device.production_state": "Production State",
		"severity_id": 					  "Severity",
		"status_change": 				  "State Change",
		"status_id": 					  "Status",
		"zenoss.device.systems": 		  "Systems",
	}

	detail_names = {
		"Device Class",
		"Systems",
		"Production State",
		"Location",
		"IP Address",
		"Groups",
		"Device Priority"
	}

	event_status_translator = {
		"New":			0,
		"Acknowledged": 1,
		"Suppressed":   3,
		"Closed":       4,
		"Cleared":      5,
		"Aged":         6
	}

	event_severity_translator = {
		"Critical":	5,
		"Error":	4,
		"Warning":	3,
		"Info":		2,
		"Debug":	1,
		"Clear":	0
	}

	device_priority_translator = {
        'Highest':  5,
        'High':     4,
        'Normal':   3,
        'Low':      2,
        'Lowest':   1,
        'Trivial':  0,
	}

	device_production_status_translator = {
        'Production':     1000,
        'Pre-Production': 500,
        'Test':           400,
        'Maintenance':    300,
        'Decommissioned': -1,
	}

	not_null_fields = {
		'uuid',
		'fingerprint',
		'status_id', 
		'event_class_id',
		'severity_id',
		'element_identifier',
		'update_time',
		'first_seen',
		'status_change',
		'last_seen',
		'event_count',
		'summary',
		'message'
	}

	null_fields = {
		'event_class_mapping_uuid',
		'element_uuid',
		'element_title',
		'element_sub_uuid',
		'element_type_id',
		'element_sub_type_id',
		'element_sub_identifier',
		'element_sub_title',
		'syslog_facility',
		'syslog_priority',
		'nt_event_code',
		'current_user_uuid',
		'current_user_name',
		'cleared_by_event_uuid',
		'details_json',
		'tags_json',
		'notes_json',
		'audit_json',
		'event_group_id',
		'event_class_key_id',
		'event_key_id',
		'monitor_id',
		'agent_id',
	}

	fields = not_null_fields | null_fields

	null_id_fields = {
		'event_group_id',
		'event_class_key_id',
		'event_key_id',
		'monitor_id',
		'agent_id',
	}

	id_tables = [
		"agent",
		"event_class",
		"event_class_key",
		"event_group",
		"event_key",
		"monitor"
	]

	def __init__(self):
		"""
		conn connection to the database
		"""
		self.config = None
		self.conn = None
		self.id_tables_loaded = False
		self.id_tables_values = {}

	def init(self, config):
		""" """
		self.config = config
		self.conn = pymysql.connect(
		    host=self.config.get('db-host', 'localhost'),
            port=self.config.get('db-port', '13306'),
            user=self.config.get('db-user', 'zenoss'),
            passwd=self.config.get('db-password', 'zenoss'),
            db=self.config.get('db-name', 'zenoss_zep'))

	def shutdown(self):
		if self.conn:
			self.conn.close()

	def _load_id_table(self, table):
		""" """
		cursor = self.conn.cursor()
		name_to_id = {}
		sql = "SELECT id, name from {0}".format(table)
		cursor.execute(sql)
		for (id, name) in cursor.fetchall():
			name_to_id[name] = id
		return name_to_id

	def _load_id_tables(self, tables):
		for table in tables:
			self.id_tables_values[table] = self._load_id_table(table)

	def _insert_in_id_table(self, table, value):
		cursor = self.conn.cursor()
		sql = "INSERT into {0} (name) VALUES ('{1}')".format(table, value)
		cursor.execute(sql)
		self.conn.commit()

	def inject_event(self, event, archive):
		""" """
		if not self.id_tables_loaded:
			self._load_id_tables(self.id_tables)
			id_tables_loaded = True

		table = "event_summary"
		if archive:
			table = "event_archive"

		ts = int(time.time()*1000)
		db_event = {}

		# NOT NULL FIELDS
		db_event['fingerprint'] = event.get(self.field_name_translator['fingerprint'], "zenoss_test_{0}".format(ts))
		db_event['status_id'] = self.event_status_translator[event.get(self.field_name_translator['status_id'], "New")]
		if archive:
			db_event['status_id'] = self.event_status_translator[event.get(self.field_name_translator['status_id'], "Closed")]
		db_event['severity_id'] = self.event_severity_translator[event.get(self.field_name_translator['severity_id'], "Error")]
		db_event['update_time'] = ts
		db_event['first_seen'] = event.get(self.field_name_translator['first_seen'], ts)
		db_event['status_change'] = event.get(self.field_name_translator['status_change'], ts)
		db_event['last_seen'] = event.get(self.field_name_translator['last_seen'], ts)
		db_event['event_count'] = event.get(self.field_name_translator['event_count'], 1)
		db_event['summary'] = event.get(self.field_name_translator['summary'], "zenoss_test: Test event")
		db_event['message'] = event.get(self.field_name_translator['message'], "zenoss_test: Test event")
		db_event['element_identifier'] = event.get(self.field_name_translator['element_identifier'], 1)

		# not null fields with an id table associated
		event_class = event.get(self.field_name_translator['event_class_id'])
		if event_class:
			if event_class not in self.id_tables_values["event_class"].keys():
				self._insert_in_id_table("event_class", event_class)
				self._load_id_tables(["event_class"])
			db_event['event_class_id'] = self.id_tables_values["event_class"][event_class]
		else:
			db_event['event_class_id'] = self.id_tables_values["event_class"].values[0]

		if event.get(self.field_name_translator['element_sub_identifier']):
			db_event['element_sub_identifier'] = event.get(self.field_name_translator['element_sub_identifier'])

		if event.get(self.field_name_translator['current_user_name']):
			db_event['current_user_name'] = event.get(self.field_name_translator['current_user_name'])

		# not null fields with an id table associated
		for field_name in self.null_id_fields:
			id_table_name =  field_name.split("_id")[0]
			field_value = event.get(self.field_name_translator[field_name])
			if field_value:
				if field_value not in self.id_tables_values[id_table_name].keys():
					self._insert_in_id_table(id_table_name, field_value)
					self._load_id_tables([id_table_name])
				db_event[field_name] = self.id_tables_values[id_table_name][field_value]

		fields = []
		values = []
		for field, value in db_event.iteritems():
			fields.append(field)
			values.append("'{0}'".format(value))

		# UUID and FINGERPRINT_HASH  NEED TO BE TREATED SEPARATELY
		event_id = uuid.uuid1()
		db_event['uuid'] = "STR_UUID_TO_BINARY('{0}')".format(event_id)
		fields.append('uuid')
		values.append(db_event['uuid'])

		if not archive:
			db_event['fingerprint_hash'] = "SHA1('{0}')".format(ts)
			fields.append('fingerprint_hash')
			values.append(db_event['fingerprint_hash'])

		details = {}
		db_detatils = []
		for detail in self.detail_names:
			if event.get(detail):
				if detail == "Production State":
					details[self.field_name_to_id_mapping[detail]] = self.device_production_status_translator[event.get(detail)]
				elif detail == "Device Priority":
					details[self.field_name_to_id_mapping[detail]] = self.device_priority_translator[event.get(detail)]
				else:
					details[self.field_name_to_id_mapping[detail]] = event.get(detail)

		for det, value in details.iteritems():
			if isinstance(value, list):
				detail = {"name": det, "value": value}
			else:
				detail = {"name": det, "value": [value]}
			db_detatils.append(detail)

		if db_detatils:
			fields.append('details_json')
			values.append("'{0}'".format(json.dumps(db_detatils)))

		sql = """ INSERT INTO {0} ({1}) VALUES ({2}) """.format(table, ','.join(fields), ','.join(values))
		cursor = self.conn.cursor()
		cursor.execute(sql)
		self.conn.commit()
		self.index(event_id, archive)

		return "{0}".format(event_id)

	def delete_event(self, event_id, archive):
		""" """
		table = "event_summary"
		if archive:
			table = "event_archive"

		sql = """ DELETE FROM {0} WHERE uuid = STR_UUID_TO_BINARY('{1}'); """.format(table, event_id)
		cursor = self.conn.cursor()
		cursor.execute(sql)
		self.conn.commit()
		self.index(event_id, archive)

	def index(self, event_id, archive):
		""" """
		ts = int(time.time()*1000)

		if archive:
			table = "event_archive_index_queue"
			fields = "uuid, last_seen, update_time"
			values = "STR_UUID_TO_BINARY('{0}'), {1}, {2}".format(event_id, ts, ts)
		else:
			table = "event_summary_index_queue"
			fields = "uuid, update_time"
			values = "STR_UUID_TO_BINARY('{0}'), {1}".format(event_id, ts)

		sql = """ INSERT INTO {0} ({1}) VALUES ({2}) """.format(table, fields, values)
		cursor = self.conn.cursor()
		cursor.execute(sql)
		self.conn.commit()
