import threading
from datetime import date, datetime, time


from main.common import create_monitoring, create_alerts
from main.models import Monitoring


class MonitoringCreationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, req):
        self.process_request(req)
        res = self.get_response(req)
        return self.process_response(req, res)

    def process_request(self, req):
        path = req.path or ''
        today = date.today()
        min_today_time = datetime.combine(today, time.min)
        if path == '/' and not Monitoring.objects.filter(day__gte=min_today_time).exists():
            threading.Thread(target=create_monitoring).start()
            threading.Thread(target=create_alerts).start()

    def process_response(self, _ , res):
        return res
