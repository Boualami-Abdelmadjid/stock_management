from main.responses import RESPONSES


def valid_permissions(user):
    return user.role == "store_manager"


def valid_action_path(action_to_check, status_to_check):
    action_paths = (
        ('receive', None, {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('receive', 'in_stock', {'valid': False, 'status': 501, 'response': RESPONSES.ALREADY_IN_STOCK}),
        ('receive', 'onboarded',
         {'valid': False, 'status': 501, 'response': RESPONSES.ONBOARDED_AND_ASSIGNED}),
        ('receive', 'returned',
         {'valid': False, 'status': 501, 'response': RESPONSES.RETURNED_BY_CUSTOMER}),
        ('receive', 'to_refurb', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),

        ('sale', None, {'valid': False, 'status': 501, 'response': RESPONSES.NOT_SCANNED}),
        ('sale', 'in_stock', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('sale', 'onboarded', {'valid': False, 'status': 501, 'response': RESPONSES.ALLOCATED_TO_ORDER}),
        ('sale', 'returned',
         {'valid': False, 'status': 501, 'response': RESPONSES.NEW_DEVICE_RETURN}),
        ('sale', 'to_refurb', {'valid': False, 'status': 501,
                               'response': RESPONSES.NEW_DEVICE_CCD}),

        ('collect', None, {'valid': False, 'status': 501, 'response': RESPONSES.NOT_SCANNED}),
        ('collect', 'in_stock', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        (
        'collect', 'onboarded', {'valid': False, 'status': 501, 'response': RESPONSES.ALLOCATED_TO_ORDER}),
        ('collect', 'returned',
         {'valid': False, 'status': 501, 'response': RESPONSES.NEW_DEVICE_RETURN}),
        ('collect', 'to_refurb', {'valid': False, 'status': 501,
                                  'response': RESPONSES.NEW_DEVICE_CCD}),

        ('swap', None, {'valid': False, 'status': 501, 'response': RESPONSES.NOT_SCANNED}),
        ('swap', 'in_stock', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('swap', 'onboarded', {'valid': False, 'status': 501, 'response': RESPONSES.ALLOCATED_TO_ORDER}),
        ('swap', 'returned',
         {'valid': False, 'status': 501, 'response': RESPONSES.NEW_DEVICE_RETURN}),
        ('swap', 'to_refurb', {'valid': False, 'status': 501,
                               'response': RESPONSES.NEW_DEVICE_CCD}),

        ('return', None, {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('return', 'in_stock', {'valid': False, 'status': 501, 'response': RESPONSES.NEVER_ASSIGNED}),
        ('return', 'onboarded', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('return', 'returned', {'valid': False, 'status': 501, 'response': RESPONSES.ALREADY_RETURNED}),
        ('return', 'to_refurb', {'valid': False, 'status': 501, 'response': RESPONSES.TO_BE_RETURNED}),

        ('out', None, {'valid': False, 'status': 501, 'response': RESPONSES.NOT_SCANNED}),
        ('out', 'in_stock', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('out', 'onboarded', {'valid': False, 'status': 501, 'response': RESPONSES.ALLOCATED_TO_ORDER}),
        ('out', 'returned',
         {'valid': False, 'status': 501, 'response': RESPONSES.NEW_DEVICE_RETURN}),
        ('out', 'to_refurb', {'valid': False, 'status': 501,
                              'response': RESPONSES.NEW_DEVICE_CCD}),

        ('transfer', None, {'valid': False, 'status': 501, 'response': RESPONSES.NOT_SCANNED}),
        ('transfer', 'in_stock', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('transfer', 'onboarded',
         {'valid': False, 'status': 501, 'response': RESPONSES.ALLOCATED_TO_ORDER}),
        ('transfer', 'returned',
         {'valid': False, 'status': 501, 'response': RESPONSES.RETURN_NOT_ELIGIBLE_FOR_TRANSFER}),
        ('transfer', 'to_refurb', {'valid': False, 'status': 501, 'response': RESPONSES.BOUND_FOR_CCD}),

        ('returned_CCD', None, {'valid': False, 'status': 501, 'response': RESPONSES.NOT_SCANNED}),
        ('returned_CCD', 'in_stock',
         {'valid': False, 'status': 501, 'response': RESPONSES.INSTOCK_NO_RETURN_TO_CCD}),
        ('returned_CCD', 'onboarded', {'valid': False, 'status': 501, 'response': RESPONSES.ALLOCATED_TO_ORDER}),
        ('returned_CCD', 'returned', {'valid': True, 'status': 200, 'response': RESPONSES.SUCCESS}),
        ('returned_CCD', 'to_refurb', {'valid': False, 'status': 501, 'response': RESPONSES.ALREADY_RETURNED}),
    )

    valid_actions = [
        action for action in action_paths if
        (action[0] == action_to_check and action[1] == status_to_check)]

    if len(valid_actions) == 1:
        return valid_actions[0][2]

    else:
        return None
