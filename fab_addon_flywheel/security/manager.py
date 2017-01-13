import logging
import uuid

from flask_appbuilder import const as c
from flask_appbuilder.security.manager import BaseSecurityManager
from werkzeug.security import generate_password_hash

from fab_addon_flywheel.models.interface import FlywheelInterface
from fab_addon_flywheel.utils import get_pk_value
from .models import Permission, PermissionView, RegisterUser, Role, User, ViewMenu

log = logging.getLogger(__name__)


class SecurityManager(BaseSecurityManager):
    """
        Responsible for authentication, registering security views,
        role and permission auto management

        If you want to change anything just inherit and override, then
        pass your own security manager to AppBuilder.
    """
    user_model = User
    """ Override to set your own User Model """
    role_model = Role
    """ Override to set your own Role Model """
    permission_model = Permission
    viewmenu_model = ViewMenu
    permissionview_model = PermissionView
    registeruser_model = RegisterUser

    generate_password_hash = generate_password_hash

    def __init__(self, appbuilder):
        """
            SecurityManager contructor
            param appbuilder:
                F.A.B AppBuilder main object
        """
        super(SecurityManager, self).__init__(appbuilder)
        user_datamodel = FlywheelInterface(self.user_model, appbuilder.get_session)
        if self.auth_type == c.AUTH_DB:
            self.userdbmodelview.datamodel = user_datamodel
        elif self.auth_type == c.AUTH_LDAP:
            self.userldapmodelview.datamodel = user_datamodel
        elif self.auth_type == c.AUTH_OID:
            self.useroidmodelview.datamodel = user_datamodel
        elif self.auth_type == c.AUTH_OAUTH:
            self.useroauthmodelview.datamodel = user_datamodel
        elif self.auth_type == c.AUTH_REMOTE_USER:
            self.userremoteusermodelview.datamodel = user_datamodel

        self.userstatschartview.datamodel = user_datamodel
        if self.auth_user_registration:
            self.registerusermodelview.datamodel = FlywheelInterface(self.registeruser_model, appbuilder.get_session)

        self.rolemodelview.datamodel = FlywheelInterface(self.role_model, appbuilder.get_session)
        self.permissionmodelview.datamodel = FlywheelInterface(self.permission_model, appbuilder.get_session)
        self.viewmenumodelview.datamodel = FlywheelInterface(self.viewmenu_model, appbuilder.get_session)
        self.permissionviewmodelview.datamodel = FlywheelInterface(self.permissionview_model, appbuilder.get_session)

        self.create_db()

    @property
    def engine(self):
        return self.appbuilder.get_session

    def register_views(self):
        super(SecurityManager, self).register_views()

    def create_db(self):
        try:
            models = [
                self.user_model, self.role_model, self.permission_model, self.viewmenu_model,
                self.permissionview_model, self.registeruser_model
            ]

            models_to_register = []
            for model in models:
                if model.meta_.name not in self.engine.models:
                    models_to_register.append(model)

            if models_to_register:
                log.info(c.LOGMSG_INF_SEC_NO_DB)
                self.engine.register(*models_to_register)
                self.engine.create_schema()
                log.info(c.LOGMSG_INF_SEC_ADD_DB)
            super(SecurityManager, self).create_db()
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_CREATE_DB.format(str(e)))
            exit(1)

    def find_register_user(self, registration_hash):
        return self.engine.scan(self.registeruser_model).filter(
            self.registeruser_model.registration_hash == registration_hash).one()

    def add_register_user(self, username, first_name, last_name, email,
                          password='', hashed_password=''):
        """
            Add a registration request for the user.

            :rtype : RegisterUser
        """
        register_user = self.registeruser_model()
        register_user.username = username
        register_user.email = email
        register_user.first_name = first_name
        register_user.last_name = last_name
        if hashed_password:
            register_user.password = hashed_password
        else:
            register_user.password = self.generate_password_hash(password)
        register_user.registration_hash = str(uuid.uuid1())
        try:
            self.engine.save(register_user, overwrite=True)
            register_user.__engine__ = self.engine
            return register_user
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_ADD_REGISTER_USER.format(str(e)))
            return None

    def del_register_user(self, register_user):
        """
            Deletes registration object from database

            :param register_user: RegisterUser object to delete
        """
        try:
            register_user.delete(raise_on_conflict=True)
            return True
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_DEL_REGISTER_USER.format(str(e)))
            return False

    def find_user(self, username=None, email=None):
        """
            Finds user by username or email
        """
        if username:
            return self.engine.scan(self.user_model).filter(self.user_model.username == username).first()
        elif email:
            return self.engine.scan(self.user_model).filter(email=email).first()

    def get_all_users(self):
        return self.engine.scan(self.user_model).all()

    def add_user(self, username, first_name, last_name, email, role, password='', hashed_password='', **kwargs):
        """
            Generic function to create user
        """
        try:
            user = self.user_model()
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.active = True
            user.roles.append(role)
            if hashed_password:
                user.password = hashed_password
            else:
                user.password = generate_password_hash(password)

            self.engine.save(user)
            user.__engine__ = self.engine
            log.info(c.LOGMSG_INF_SEC_ADD_USER.format(username))
            return user
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_ADD_USER.format(str(e)))
            return False

    def count_users(self):
        return self.engine.scan(self.user_model).count()

    def update_user(self, user):
        try:
            user.sync(raise_on_conflict=True)
            log.info(c.LOGMSG_INF_SEC_UPD_USER.format(user))
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_UPD_USER.format(str(e)))
            return False

    def get_user_by_id(self, pk):
        return self.engine.scan(self.user_model).filter(get_pk_value(self.user_model) == pk).one()

    """
        ----------------------------------------
            PERMISSION MANAGEMENT
        ----------------------------------------
    """
    def add_role(self, name):
        role = self.find_role(name)
        if role is None:
            try:
                role = self.role_model()
                role.name = name
                self.engine.save(role)
                role.__engine__ = self.engine
                log.info(c.LOGMSG_INF_SEC_ADD_ROLE.format(name))
                return role
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_ADD_ROLE.format(str(e)))
        return role

    def find_role(self, name):
        return self.engine.scan(self.role_model).filter(name=name).first()

    def get_all_roles(self):
        return self.engine.scan(self.role_model).all()

    def get_public_permissions(self):
        role = self.engine.scan(self.role_model).filter(name=self.auth_role_public).first()
        return role.permissions

    def find_permission(self, name):
        """
            Finds and returns a Permission by name
        """
        return self.engine.scan(self.permission_model).filter(name=name).first()

    def add_permission(self, name):
        """
            Adds a permission to the backend, model permission

            :param name:
                name of the permission: 'can_add','can_edit' etc...
        """
        perm = self.find_permission(name)
        if perm is None:
            try:
                perm = self.permission_model()
                perm.name = name
                self.engine.save(perm)
                perm.__engine__ = self.engine
                return perm
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_ADD_PERMISSION.format(str(e)))
        return perm

    def del_permission(self, name):
        """
            Deletes a permission from the backend, model permission

            :param name:
                name of the permission: 'can_add','can_edit' etc...
        """
        perm = self.find_permission(name)
        if perm:
            try:
                self.engine.delete(perm)
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_DEL_PERMISSION.format(str(e)))

    # ----------------------------------------------
    #       PRIMITIVES VIEW MENU
    # ----------------------------------------------
    def find_view_menu(self, name):
        """
            Finds and returns a ViewMenu by name
        """
        return self.engine.scan(self.viewmenu_model).filter(name=name).first()

    def get_all_view_menu(self):
        return self.engine.scan(self.viewmenu_model).all()

    def add_view_menu(self, name):
        """
            Adds a view or menu to the backend, model view_menu
            param name:
                name of the view menu to add
        """
        view_menu = self.find_view_menu(name)
        if view_menu is None:
            try:
                view_menu = self.viewmenu_model()
                view_menu.name = name
                self.engine.save(view_menu)
                view_menu.__engine__ = self.engine
                return view_menu
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_ADD_VIEWMENU.format(str(e)))
        return view_menu

    def del_view_menu(self, name):
        """
            Deletes a ViewMenu from the backend

            :param name:
                name of the ViewMenu
        """
        obj = self.find_view_menu(name)
        if obj:
            try:
                self.engine.delete(obj)
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_DEL_PERMISSION.format(str(e)))

    # ----------------------------------------------
    #          PERMISSION VIEW MENU
    # ----------------------------------------------
    def find_permission_view_menu(self, permission_name, view_menu_name):
        """
            Finds and returns a PermissionView by names
        """
        permission = self.find_permission(permission_name)
        view_menu = self.find_view_menu(view_menu_name)
        return self.engine.scan(self.permissionview_model).filter(permission=permission, view_menu=view_menu).first()

    def find_permissions_view_menu(self, view_menu):
        """
            Finds all permissions from ViewMenu, returns list of PermissionView

            :param view_menu: ViewMenu object
            :return: list of PermissionView objects
        """
        return self.engine.scan(self.permissionview_model).filter(view_menu_id=view_menu.id).all()

    def add_permission_view_menu(self, permission_name, view_menu_name):
        """
            Adds a permission on a view or menu to the backend

            :param permission_name:
                name of the permission to add: 'can_add','can_edit' etc...
            :param view_menu_name:
                name of the view menu to add
        """
        vm = self.add_view_menu(view_menu_name)
        perm = self.add_permission(permission_name)
        pv = self.permissionview_model()
        pv.view_menu_id, pv.permission_id = vm.id, perm.id
        try:
            self.engine.save(pv)
            pv.__engine__ = self.engine
            log.info(c.LOGMSG_INF_SEC_ADD_PERMVIEW.format(str(pv)))
            return pv
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_ADD_PERMVIEW.format(str(e)))

    def del_permission_view_menu(self, permission_name, view_menu_name):
        try:
            pv = self.find_permission_view_menu(permission_name, view_menu_name)
            # delete permission on view
            self.engine.delete(pv)
            # if no more permission on permission view, delete permission
            pv = self.engine.scan(self.permissionview_model).filter(permission=pv.permission).all()
            if not pv:
                self.del_permission(pv.permission.name)
            log.info(c.LOGMSG_INF_SEC_DEL_PERMVIEW.format(permission_name, view_menu_name))
        except Exception as e:
            log.error(c.LOGMSG_ERR_SEC_DEL_PERMVIEW.format(str(e)))

    def exist_permission_on_views(self, lst, item):
        for i in lst:
            if i.permission.name == item:
                return True
        return False

    def exist_permission_on_view(self, lst, permission, view_menu):
        for i in lst:
            if i.permission.name == permission and i.view_menu.name == view_menu:
                return True
        return False

    def add_permission_role(self, role, perm_view):
        """
            Add permission-ViewMenu object to Role

            :param role:
                The role object
            :param perm_view:
                The PermissionViewMenu object
        """
        if perm_view not in role.permissions:
            try:
                role.permissions.append(perm_view)
                self.engine.sync(role)
                role.__engine__ = self.engine
                log.info(c.LOGMSG_INF_SEC_ADD_PERMROLE.format(str(perm_view), role.name))
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_ADD_PERMROLE.format(str(e)))

    def del_permission_role(self, role, perm_view):
        """
            Remove permission-ViewMenu object to Role

            :param role:
                The role object
            :param perm_view:
                The PermissionViewMenu object
        """
        if perm_view in role.permissions:
            try:
                role.permissions.remove(perm_view)
                self.engine.sync(role)
                log.info(c.LOGMSG_INF_SEC_DEL_PERMROLE.format(str(perm_view), role.name))
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_DEL_PERMROLE.format(str(e)))
