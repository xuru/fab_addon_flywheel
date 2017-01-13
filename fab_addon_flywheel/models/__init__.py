from flywheel import Model as BaseModel


class Model(BaseModel):

    __metadata__ = {
        '_abstract': True,
    }

    @property
    def engine(self):
        return self.__engine__

    def get_related_models(self, field_name):
        prop = self.field_(field_name)
        model = self.engine.models.get(prop.metadata.get('model'))
        pk_name = model.meta_.hash_key.name
        if prop.is_set:
            return self.engine.query(model).filter(model.field_(pk_name).in_(prop)).all()
        else:
            return self.engine.query(model).filter(getattr(model, pk_name) == prop).first()

    def set_related_models(self, field_name, items):
        prop = self.field_(field_name)
        model = self.engine.models.get(prop.metadata.get('model'))
        pk_name = model.meta_.hash_key.name

        if prop.is_set:
            for item in items:
                if getattr(item, pk_name) not in prop:
                    prop.add(getattr(item, pk_name))
        else:
            prop = getattr(items, pk_name)
        return prop

