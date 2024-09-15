from orders.models import OrderLogModel

def log_operate(operator_id, operation):
    OrderLogModel.objects.create(operator_id=operator_id, operation=operation)