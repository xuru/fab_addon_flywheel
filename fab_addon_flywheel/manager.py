import logging
from flask.ext.appbuilder.basemanager import BaseManager

log = logging.getLogger(__name__)


class FlywheelAddOnManager(BaseManager):

    def __init__(self, appbuilder):
        """
             Use the constructor to setup any config keys specific for your app.
        """
        super(FlywheelAddOnManager, self).__init__(appbuilder)

    def register_views(self):
        """
            This method is called by AppBuilder when initializing, use it to add you views
        """
        pass

    def pre_process(self):
        pass

    def post_process(self):
        pass
