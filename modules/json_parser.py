from datetime import date, datetime, timezone


class Json_Parser:

    """
    Gets the requested json battle info between a given time.

    Will return True w/ the corresponding battle json info if one can be found
    Will return False w/ null if one could not be found
    """
def get_requ_battle(json_data, time_requ=None):
    for val in json_data:
        if time_requ is None:
            local_time = int(datetime.now(tz=timezone.utc).timestamp())
        else
            local_time = time_requ
        start_time = date.fromtimestamp(val['start_time'])
        end_time = date.fromtimestamp(val['end_time'])

        if start_time <= local_time <= end_time:
            # Valid battle info, return battle json info
            return True, val
        else:
            # Was invalid, try again
            continue
    # No valid battle info found
    return False, None
