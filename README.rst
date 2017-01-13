F.A.B. AddOn - Flywheel
-----------------------

Adds support for Flywheel to F.A.B.

- Install it::

	pip install fab-addon-flywheel

- Use it:

In your application, add the following key to **config.py**::


    ADDON_MANAGERS = ['fab_addon_flywheel.manager.FlywheelAddOnManager']


In your application change your views.py file to import::


    from fab_addon_flywheel.security.manager import SecurityManager

    appbuilder = AppBuilder(app, db.engine, security_manager_class=SecurityManager)


There are a few assumptions that are made...
