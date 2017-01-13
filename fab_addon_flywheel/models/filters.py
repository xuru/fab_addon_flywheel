import logging
from flask_babel import lazy_gettext
from flask_appbuilder.models.filters import BaseFilter, FilterRelation, BaseFilterConverter

log = logging.getLogger(__name__)

__all__ = [
    'FlywheelFilterConverter',
    'FilterEqual', 'FilterNotEqual',
    'FilterGreater', 'FilterSmaller',
    'FilterContains', 'FilterNotContains',
    'FilterIn', 'FilterBetween',
    'FilterStartsWith', 'FilterContains', 'FilterNotContains',
    'FilterRelationOneToManyEqual', 'FilterRelationManyToManyEqual',
    'FilterEqualFunction', 'FilterInFunction'
]


class BaseFlywheelFilter(BaseFilter):

    def apply(self, query, value):
        raise NotImplementedError

    @property
    def field(self):
        return getattr(self.model, self.column_name)


class FilterEqual(BaseFlywheelFilter):
    name = lazy_gettext('Equal to')

    def apply(self, query, value):
        if self.datamodel.is_boolean(self.column_name):
            if value == 'y':
                value = True
        return query.filter(self.field == value)


class FilterNotEqual(BaseFlywheelFilter):
    name = lazy_gettext('Not Equal to')

    def apply(self, query, value):
        if self.datamodel.is_boolean(self.column_name):
            if value == 'y':
                value = True
        return query.filter(self.field != value)


class FilterGreater(BaseFlywheelFilter):
    name = lazy_gettext('Greater Than')

    def apply(self, query, value):
        return query.filter(self.field > value)


class FilterGreaterOrEqual(BaseFlywheelFilter):
    name = lazy_gettext('Greater Than or Equal')

    def apply(self, query, value):
        return query.filter(self.field >= value)


class FilterSmaller(BaseFlywheelFilter):
    name = lazy_gettext('Smaller Than')

    def apply(self, query, value):
        return query.filter(self.field < value)


class FilterSmallerEqual(BaseFlywheelFilter):
    name = lazy_gettext('Smaller Than or Equal')

    def apply(self, query, value):
        return query.filter(self.field <= value)


class FilterIn(BaseFlywheelFilter):
    name = lazy_gettext('In')

    def apply(self, query, value):
        if self.datamodel.is_text(self.column_name) or self.datamodel.is_string(self.column_name):
            return query.filter(self.field.in_(value))
        return query.filter(self.field.in_(value or [None]))


class FilterBetween(BaseFlywheelFilter):
    name = lazy_gettext('Between')

    def apply(self, query, value):
        start, end = value
        return query.filter(self.field.between_(start, end))


class FilterStartsWith(BaseFlywheelFilter):
    name = lazy_gettext('Starts with')

    def apply(self, query, value):
        return query.filter(self.field.beginswith_(value))


class FilterContains(BaseFlywheelFilter):
    name = lazy_gettext('Contains')

    def apply(self, query, value):
        return query.filter(self.field.contains_(value))


class FilterNotContains(BaseFlywheelFilter):
    name = lazy_gettext('Not Contains')

    def apply(self, query, value):
        return query.filter(self.field.ncontains_(value))


class FilterRelationOneToManyEqual(FilterRelation, BaseFlywheelFilter):
    name = lazy_gettext('Relation')

    def apply(self, query, value):
        rel_obj = self.datamodel.get_related_obj(self.column_name, value)
        return query.filter(self.field == rel_obj)


class FilterRelationManyToManyEqual(FilterRelation, BaseFlywheelFilter):
    name = lazy_gettext('Relation as Many')

    def apply(self, query, value):
        rel_obj = self.datamodel.get_related_obj(self.column_name, value)
        return query.filter(self.field == rel_obj)


class FilterEqualFunction(BaseFlywheelFilter):
    name = "Filter view with a function"

    def apply(self, query, func):
        return query.filter(self.field == func())


class FilterInFunction(BaseFlywheelFilter):
    name = "Filter view where field is in a list returned by a function"

    def apply(self, query, func):
        return query.filter(self.field.in_(func()))


class FlywheelFilterConverter(BaseFilterConverter):
    """
        Class for converting columns into a supported list of filters
        specific for SQLAlchemy.

    """
    _str_fltrs = [
        FilterEqual, FilterNotEqual,
        FilterSmaller, FilterGreater, FilterSmallerEqual, FilterGreaterOrEqual,
        FilterIn, FilterBetween, FilterStartsWith
    ]

    _num_fltrs = [
        FilterEqual, FilterNotEqual,
        FilterSmaller, FilterGreater, FilterSmallerEqual, FilterGreaterOrEqual,
        FilterIn, FilterBetween
    ]

    conversion_table = (
        ('is_relation_many_to_one', [FilterRelationOneToManyEqual]),
        ('is_relation_one_to_one', [FilterRelationOneToManyEqual]),
        ('is_relation_many_to_many', [FilterRelationManyToManyEqual]),
        ('is_relation_one_to_many', [FilterRelationManyToManyEqual]),
        ('is_object_id', [FilterEqual]),
        ('is_string', _str_fltrs),
        ('is_text', _str_fltrs),
        ('is_boolean', [FilterEqual, FilterNotEqual]),
        ('is_datetime', [FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller]),
        ('is_integer', _num_fltrs),
        ('is_numeric', _num_fltrs),
        ('is_float', _num_fltrs),
        ('is_date', [FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller]),
        ('is_datetime', [FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller]),
    )
