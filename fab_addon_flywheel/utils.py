from dynamo3 import Limit


class FlywheelPager:
    def __init__(self, model, query, page_size=0, sort_field=None, sort_desc=None):
        self.model = model
        self.query = query
        self.curr_page = 0
        self.page_size = page_size
        self.sort_field = sort_field
        self.sort_desc = sort_desc
        self.keys = {0: None}
        self.last_evaluated_key = None
        self.set_page_size(page_size)

    def set_page_size(self, page_size):
        if page_size:
            self.query = self.query.limit(Limit(item_limit=page_size, strict=True))

    def reset(self):
        self.keys = {0: None}

    def _get_page(self, page_num):
        if page_num not in self.keys:
            self._get_page(page_num - 1)
        key = self.keys[page_num]
        results = self.query.all(exclusive_start_key=key)
        if results:
            self.keys[page_num+1] = self.model.meta_.pk_dict(results[-1], ddb_dump=True)
        return results

    def page(self, page_num):
        results = self._get_page(page_num)

        if self.sort_field is not None:
            results = sorted(results, key=lambda x: getattr(x, self.sort_field), reverse=self.sort_desc)
        return results


def get_primary_key(model):
    return model.meta_.hash_key.name


def get_pk_value(model):
    return getattr(model, model.meta_.hash_key.name)


def construct_keys_list(pk_name, value):
    # TODO: support compound key stuff
    key = {pk_name: value}
    return [key]


def get_model_fields(model):
    return model.meta_.fields


def get_sorted_fields(model):
    pk_name = model.meta_.hash_key.name
    keys = sorted(model.meta_.fields.keys())
    return [model.meta_.hash_key] + [model.meta_.fields[n] for n in keys if n != pk_name]


class FlywheelQueryHelper:
    def __init__(self, engine, model, page_size=0):
        self.flywheel_pager = None
        self.engine = engine
        self.model = model
        self.page_size = page_size

    def get_fields(self, model=None):
        if model is None:
            model = self.model
        return model.meta_.fields.values()

    def get_field_names(self, model=None):
        if model is None:
            model = self.model
        return model.meta_.fields.keys()

    def get_pk_name(self, model=None):
        if model is None:
            model = self.model
        return model.meta_.hash_key.name

    def get_pk_field(self, model=None):
        if model is None:
            model = self.model
        return getattr(model, model.meta_.hash_key.name)

    def get_field(self, name):
        return self.model.field_(name)

    def get_field_type(self, name):
        field = self.get_field(name)
        if field.is_set:
            return field.data_type.item_type
        return field.data_type.data_type

    def get_related(self, name):
        field = self.get_field(name)
        if 'model' in field.metadata:
            return self.engine.models.get(field.metadata.get('model'))

    def get_one(self, pk_value, model=None):
        if model is None:
            model = self.model
        value = self.model.meta_.hash_key.data_type.data_type(pk_value)
        pk_name = get_primary_key(model)
        keys = construct_keys_list(pk_name, value)
        return self.engine.query(model).filter(**keys[0]).one()

    def get_scan(self, model=None):
        if model is None:
            model = self.model
        return self.engine.scan(model)

    def get_query(self, model=None):
        if model is None:
            model = self.model
        return self.engine.query(model)

    def get_all(self, model=None):
        if model is None:
            model = self.model
        return self.engine.query(model).all()

    def get_list(self, page=0, sort_field=None, sort_desc=False, query=None, page_size=0, **kwargs):

        if page_size != self.page_size:
            self.page_size = page_size

        if query is None:
            query = self.get_scan()
            self.flywheel_pager = None

        # TODO: Search
        # TODO: Filters

        simple_list_pager = kwargs['simple_list_pager'] if 'simple_list_pager' in kwargs else False

        # Get count
        count = query.count() if simple_list_pager is False else None

        # Pagination
        if self.flywheel_pager is None:
            self.flywheel_pager = FlywheelPager(self.model, query, self.page_size, sort_field, sort_desc)

        return count, self.flywheel_pager.page(page)
