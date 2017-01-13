# -*- coding: utf-8 -*-
import logging
import sys

import flywheel

from fab_addon_flywheel import utils
from flask_appbuilder._compat import as_unicode
from flask_appbuilder.const import LOGMSG_ERR_DBI_ADD_GENERIC, LOGMSG_ERR_DBI_DEL_GENERIC, \
    LOGMSG_ERR_DBI_EDIT_GENERIC
from flask_appbuilder.models.base import BaseInterface

from fab_addon_flywheel.models import filters
from fab_addon_flywheel.utils import FlywheelQueryHelper

log = logging.getLogger(__name__)


def _include_filters(obj):
    for key in filters.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(filters, key))


# noinspection PyBroadException
class FlywheelInterface(BaseInterface):
    """
    FlywheelModel
    Implements Flywheel support methods for views
    """
    session = None

    filter_converter_class = filters.FlywheelFilterConverter

    def __init__(self, obj, engine=None):
        self.session = engine
        self.helper = FlywheelQueryHelper(engine, obj)
        _include_filters(self)
        super(FlywheelInterface, self).__init__(obj)

    @property
    def model_name(self):
        """
            Returns the models class name
            useful for auto title on views
        """
        return self.obj.__name__

    def query(self, filters=None, order_column='', order_direction='', page=None, page_size=None):

        # base query
        query = self.helper.get_scan()

        # apply filters
        if filters:
            query = filters.apply_all(query)

        return self.helper.get_list(page, page_size=page_size, sort_field=order_column, sort_desc=order_direction,
                                    query=query)

    """
    -----------------------------------------
         FUNCTIONS for Testing TYPES
    -----------------------------------------
    """

    def is_object_id(self, col_name):
        try:
            return col_name == self.helper.get_pk_name()
        except Exception as e:
            return False

    def is_string(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.StringType)
        except Exception as e:
            return False

    def is_text(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.BinaryType)
        except Exception as e:
            return False

    def is_integer(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.IntType)
        except Exception as e:
            return False

    def is_numeric(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.NumberType)
        except Exception as e:
            return False

    def is_float(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.FloatType)
        except Exception as e:
            return False

    def is_boolean(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.BoolType)
        except Exception as e:
            return False

    def is_date(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.DateType)
        except Exception as e:
            return False

    def is_datetime(self, col_name):
        try:
            return isinstance(self.helper.get_field_type(col_name), flywheel.fields.types.DateTimeType)
        except Exception as e:
            return False

    def is_relation(self, col_name):
        return 'model' in self.helper.get_field(col_name).metadata

    def is_relation_many_to_one(self, col_name):
        return self.is_relation(col_name) and not self.helper.get_field(col_name).is_set

    def is_relation_many_to_many(self, col_name):
        return self.is_relation(col_name) and self.helper.get_field(col_name).is_set

    def is_relation_one_to_one(self, col_name):
        return self.is_relation(col_name) and not self.helper.get_field(col_name).is_set

    def is_relation_one_to_many(self, col_name):
        return self.is_relation(col_name) and self.helper.get_field(col_name).is_set

    def is_pk(self, col_name):
        return self.helper.get_pk_name() == col_name

    def is_fk(self, col_name):
        return True if self.helper.get_related(col_name) else False

    """
    -----------------------------------------
           FUNCTIONS FOR CRUD OPERATIONS
    -----------------------------------------
    """

    def add(self, item):
        try:
            item.save()
            self.message = (as_unicode(self.add_row_message), 'success')
            return True
        except Exception as e:
            self.message = (as_unicode(self.general_error_message + ' ' + str(sys.exc_info()[0])), 'danger')
            log.exception(LOGMSG_ERR_DBI_ADD_GENERIC.format(str(e)))
            return False

    def edit(self, item):
        try:
            item.sync(raise_on_conflict=True)
            self.message = (as_unicode(self.edit_row_message), 'success')
            return True
        except Exception as e:
            self.message = (as_unicode(self.general_error_message + ' ' + str(sys.exc_info()[0])), 'danger')
            log.exception(LOGMSG_ERR_DBI_EDIT_GENERIC.format(str(e)))
            return False

    def delete(self, item):
        try:
            item.delete()
            self.message = (as_unicode(self.delete_row_message), 'success')
            return True
        except Exception as e:
            self.message = (as_unicode(self.general_error_message + ' ' + str(sys.exc_info()[0])), 'danger')
            log.exception(LOGMSG_ERR_DBI_DEL_GENERIC.format(str(e)))
            return False

    def delete_all(self, items):
        try:
            keys = []
            for item in items:
                pk_name = utils.get_primary_key(item)
                keys.extend(utils.construct_keys_list(pk_name, utils.get_pk_value(item)))
            self.session.delete(self.obj, keys)

            self.message = (as_unicode(self.delete_row_message), 'success')
            return True
        except Exception as e:
            self.message = (as_unicode(self.general_error_message + ' ' + str(sys.exc_info()[0])), 'danger')
            log.exception(LOGMSG_ERR_DBI_DEL_GENERIC.format(str(e)))
            self.session.rollback()
            return False

    """
    -----------------------------------------
         FUNCTIONS FOR RELATED MODELS
    -----------------------------------------
    """

    def get_col_default(self, col_name):
        default = getattr(self.helper.get_field(col_name), 'default', None)
        if default is not None:
            return default

    def get_related_model(self, col_name):
        return self.helper.get_related(col_name)

    def query_model_relation(self, col_name):
        model = self.get_related_model(col_name)
        return self.helper.get_all(model)

    def get_related_interface(self, col_name):
        return self.__class__(self.get_related_model(col_name), self.session)

    def get_related_obj(self, col_name, value):
        rel_model = self.get_related_model(col_name)
        return self.helper.get_one(rel_model, value)

    def get_related_fks(self, related_views):
        return [view.datamodel.get_related_fk(self.obj) for view in related_views]

    def get_related_fk(self, model):
        for col_name in self.helper.get_field_names():
            if self.is_relation(col_name):
                if model == self.get_related_model(col_name):
                    return col_name

    """
    ----------- GET METHODS -------------
    """

    def get_pk_name(self, item):
        self.helper.get_pk_name(item)

    def get_columns_list(self):
        """
            Returns all model's columns on SQLA properties
        """
        return self.helper.get_field_names()

    def get_user_columns_list(self):
        """
            Returns all model's columns except pk or fk
        """
        ret_lst = list()
        for col_name in self.get_columns_list():
            if (not self.is_pk(col_name)) and (not self.is_fk(col_name)):
                ret_lst.append(col_name)
        return ret_lst

    # TODO get different solution, more integrated with filters
    def get_search_columns_list(self):
        ret_lst = list()
        for col_name in self.get_columns_list():
            if not self.is_relation(col_name) and (not self.is_pk(col_name)) and (not self.is_boolean(col_name)):
                ret_lst.append(col_name)
            else:
                ret_lst.append(col_name)
        return ret_lst

    def get_order_columns_list(self, list_columns=None):
        """
            Returns the columns that can be ordered

            :param list_columns: optional list of columns name, if provided will
                use this list only.
        """
        ret_lst = list()
        list_columns = list_columns or self.get_columns_list()
        for col_name in list_columns:
            if not self.is_relation(col_name):
                ret_lst.append(col_name)
        return ret_lst


"""
    For Retro-Compatibility
"""
SQLModel = FlywheelInterface
