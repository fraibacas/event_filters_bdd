
from behave import *
import time

@given('I can connect to the ZEP API')
def step_impl(context):
	""" """
	assert context.zenoss_test_helper.is_zep_router_available() is True

@given('the sample events have been loaded and indexed')
def step_impl(context):
	""" """
	if context.created_events:
		return True
	# Create the sample events in both summary and archive
	events = context.zenoss_test_helper.load_sample_events()
	uuids = []

	# Lets create the events
	for event in events:
		event_id = event['event_id']
		if not context.archive and event.get("Status"): # Hack to change closed and aged status or the events could be archived during test
			if event.get("Status") == "Closed":
				event["Status"] = "New"
			elif event.get("Status") == "Aged":
				event["Status"] = "Acknowledged"
		context.event_data[event_id] = event
		uuid = context.zenoss_test_helper.create_event(event, context.archive)
		context.created_events[event_id] = uuid
		uuids.append(uuid)

	# Lets wait until events are indexed
	ready = False
	deadline = time.time() + 180
	while time.time() < deadline:
		time.sleep(0.5)
		if context.zenoss_test_helper.are_uuids_indexed(uuids, context.archive):
			ready = True
			break

	assert ready is True

@given('I add the internal event uuid for "{event_id}" as filter to narrow down the search')
def step_impl(context, event_id):
	""" """
	uuid = context.created_events[event_id]
	context.current_filter["Event ID"] = uuid

@given('I add "{field_filter}" as filter for the "{field}" field which should match "{event_id}"')
def step_impl(context, field_filter, field, event_id):
	""" """
	if field=="Event ID":
		event_uuid = context.created_events[event_id]
		# We do not use the passed value since the event uuid is not known until we
		# create the event
		field_filter = event_uuid
		if "Partial string search from beginning" in context.scenario.name:
			field_filter = event_uuid[:5]
		elif "Partial string search not from beginning" in context.scenario.name:
			field_filter = event_uuid[2:6]
		elif "String search with wildcard '*'" in context.scenario.name:
			field_filter = "{0}{1}{2}".format(event_uuid[:2] , '*', event_uuid[6:])
	context.current_filter[field] = field_filter

@when('I send the request to the ZEP API')
def step_impl(context):
    context.zep_response = context.zenoss_test_helper.send_event_filter_request(context.current_filter, context.archive)
    assert context.zep_response.get("success") is True

def _get_uuids_from_event_ids(context, event_ids):
	"""
	event_ids is a string containing a list of event_ids separated by commas
	"""
	uuids = []
	if event_ids != '""':
		for ev_id in event_ids.split(','):
			event_id = ev_id.strip()
			uuid = context.created_events[event_id]
			uuids.append(uuid)
	return uuids

@then('I can see "{event_ids}" in the response')
def step_impl(context, event_ids):
	uuids = _get_uuids_from_event_ids(context, event_ids)
	found_uuids = context.zenoss_test_helper.get_uuids_from_response(context.zep_response)
	assert all(x in found_uuids for x in uuids) is True

@then('I can not see "{event_ids}" in the response')
def step_impl(context, event_ids):
	uuids = _get_uuids_from_event_ids(context, event_ids)
	found_uuids = context.zenoss_test_helper.get_uuids_from_response(context.zep_response)
	assert all(x not in found_uuids for x in uuids) is True

@given('I use the Summary field to filter only the relevant events')
def step_impl(context):
	""" """
	context.current_filter["Summary"] = "zenoss_test"

@when('I add the OR filter "{or_filter}" for the "{field}" field')
def step_impl(context, or_filter, field):
	""" """
	if field == "Event ID":
		# replace the dummy event_ids from the scenario for the real ones
		event_id_1 = context.current_scenario_data["event_id_1"]
		event_id_2 = context.current_scenario_data["event_id_2"]
		uuid_1 = context.created_events[event_id_1]
		uuid_2 = context.created_events[event_id_2]
		or_filter = "{0} || {1}".format(uuid_1, uuid_2)
	elif field == "Summary":
		# we previously set a common filter in Summary
		if context.current_filter["Summary"]:
			or_filter = " || {0}".format(or_filter)

	context.current_filter[field] = or_filter

@when('I add the NOT filter "{not_filter}" for the "{field}" field to exclude "{event_id}"')
def step_impl(context, not_filter, field, event_id):
	""" """
	if field == "Event ID":
		uuid = context.created_events[event_id]
		not_filter = "!!{0}".format(uuid)
	elif field == "Summary":
		# we previously set a common filter in Summary, we want to preserve it
		if context.current_filter["Summary"]:
			not_filter = "{0} {1}".format("zenoss_test", not_filter)
	context.current_filter[field] = not_filter


@when('I send a request sorting "{field}" in "{sort_dir}" order')
def step_impl(context, field, sort_dir):
	sort_dir = 'ASC'
	if sort_dir == "descending":
		sort_dir = 'DESC'
	sort = {"sort": field, "dir": sort_dir}
	context.zep_response = context.zenoss_test_helper.send_event_filter_request(context.current_filter, context.archive, sort)
	assert context.zep_response.get("success") is True

@then('I see "{event_id_1}" above "{event_id_2}"')
def step_impl(context, event_id_1, event_id_2):
	""" """
	event_id_1 = context.current_scenario_data["event_id_1"]
	event_id_2 = context.current_scenario_data["event_id_2"]
	uuid_1 = context.created_events[event_id_1]
	uuid_2 = context.created_events[event_id_2]
	uuids = context.zenoss_test_helper.get_uuids_from_response(context.zep_response)
	assert uuids.index(uuid_1) < uuids.index(uuid_2)

@given('the following events have been created and indexed')
def step_impl(context):
	# this has already tested in @given('the sample events have been loaded and indexed')
	pass

@when('I add "{field_filter}" as filter for the "{field}"')
def step_impl(context, field_filter, field):
	context.current_filter[field] = field_filter

