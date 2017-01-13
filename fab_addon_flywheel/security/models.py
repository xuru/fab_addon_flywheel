import uuid
import datetime
from flask import g
from fab_addon_flywheel import Field

from flask_appbuilder._compat import as_unicode
from fab_addon_flywheel import set_

from insitome.admin.appbuilder.models.flywheel import Model

_dont_audit = False


def gen_id():
    return str(uuid.uuid4().hex)


def get_user():
    return g.user.id


class Permission(Model):
    id = Field(type=str, default=gen_id, hash_key=True)
    name = Field(type=str, nullable=False)

    def __repr__(self):
        return self.name


class ViewMenu(Model):
    id = Field(type=str, default=gen_id, hash_key=True)
    name = Field(type=str, nullable=False)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)) and (self.name == other.name)

    def __neq__(self, other):
        return self.name != other.name

    def __repr__(self):
        return self.name


class PermissionView(Model):
    id = Field(type=str, default=gen_id, hash_key=True)
    permission_id = Field(type=str, model='Permission')
    view_menu_id = Field(type=str, model='ViewMenu')

    @property
    def permission(self):
        return self.get_related_models("permission_id")

    @permission.setter
    def permission(self, value):
        self.set_related_models("permission_id", value)

    @property
    def view_menu(self):
        return self.get_related_models("view_menu_id")

    @view_menu.setter
    def view_menu(self, value):
        self.set_related_models("view_menu_id", value)

    def __repr__(self):
        return str(self.permission).replace('_', ' ') + ' on ' + str(self.view_menu)


class Role(Model):
    id = Field(type=str, default=gen_id, hash_key=True)
    name = Field(type=str, nullable=False)
    permission_ids = Field(type=set_(str), model='Permission')

    @property
    def permissions(self):
        return self.get_related_models("permission_ids")

    @permissions.setter
    def permissions(self, value):
        self.set_related_models("permission_ids", value)

    def __repr__(self):
        return self.name


class User(Model):
    id = Field(type=str, default=gen_id, hash_key=True)
    first_name = Field(type=str, nullable=False)
    last_name = Field(type=str, nullable=False)
    username = Field(type=str, nullable=False)
    password = Field(type=str)
    active = Field(type=bool)
    email = Field(type=str, nullable=False)
    last_login = Field(type=datetime.datetime)
    login_count = Field(type=int)
    fail_login_count = Field(type=int)
    created_on = Field(type=datetime.datetime, default=datetime.datetime.now, nullable=True)
    changed_on = Field(type=datetime.datetime, default=datetime.datetime.now, nullable=True)
    role_ids = Field(type=set_(str), model="Role")
    created_by_id = Field(type=str, default=get_user, nullable=True, model="User")
    changed_by_id = Field(type=str, default=get_user, nullable=True, model="User")

    @property
    def roles(self):
        return self.get_related_models("role_ids")

    @roles.setter
    def roles(self, value):
        self.set_related_models("role_ids", value)

    @property
    def created_by(self):
        return self.get_related_models("created_by_id")

    @created_by.setter
    def created_by(self, value):
        self.set_related_models("created_by_id", value)

    @property
    def changed_by(self):
        return self.get_related_models("changed_by_id")

    @changed_by.setter
    def changed_by(self, value):
        self.set_related_models("changed_by_id", value)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return as_unicode(self.id)

    def get_full_name(self):
        return u'{0} {1}'.format(self.first_name, self.last_name)

    def __repr__(self):
        return self.get_full_name()


class RegisterUser(Model):
    id = Field(type=str, default=gen_id, hash_key=True)
    first_name = Field(type=str, nullable=False)
    last_name = Field(type=str, nullable=False)
    username = Field(type=str, nullable=False)
    password = Field(type=str)
    email = Field(type=str, nullable=False)
    registration_date = Field(type=datetime.datetime, default=datetime.datetime.now, nullable=True)
    registration_hash = Field(type=str)
