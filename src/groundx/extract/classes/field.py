import dateparser, typing

from pydantic import BaseModel


class ExtractedField(BaseModel):
    confidence: typing.Optional[str] = None
    conflicts: typing.List[typing.Any] = []
    key: str

    value: typing.Union[str, float, typing.List[typing.Any]] = ""

    def __init__(
        self,
        value: typing.Union[str, float, typing.List[typing.Any]],
        **data: typing.Any,
    ):
        super().__init__(**data)

        self.set_value(value)

    def contains(self, other: "ExtractedField") -> bool:
        self_val = self.get_value()
        other_val = other.get_value()
        if not (isinstance(self_val, (str, float, int))):
            raise Exception(f"unexpected self field value type [{type(self_val)}]")

        if self.equal_to_value(other_val):
            return True

        if other_val in self.conflicts:
            return True

        return False

    def equal_to_field(self, other: "ExtractedField") -> bool:
        self_val = self.get_value()
        other_val = other.get_value()
        if not (isinstance(self_val, (str, float, int))):
            raise Exception(f"unexpected self field value type [{type(self_val)}]")

        return self.equal_to_value(other_val)

    def equal_to_value(self, other: typing.Any) -> bool:
        if not (isinstance(other, (str, float, int))):
            raise Exception(f"unexpected value type [{type(other)}]")

        exist = self.get_value()
        if isinstance(exist, int):
            exist = float(exist)
        if isinstance(other, int):
            other = float(other)
        if isinstance(exist, str):
            exist = exist.lower()
        if isinstance(other, str):
            other = other.lower()

        return type(other) == type(exist) and other == exist

    def get_value(self) -> typing.Union[str, float, typing.List[typing.Any]]:
        return self.value

    def remove_conflict(self, value: typing.Any) -> None:
        if value in self.conflicts:
            self.conflicts.remove(value)
        if not self.equal_to_value(value):
            self.conflicts.append(self.get_value())

    def set_value(
        self, value: typing.Union[str, float, typing.List[typing.Any]]
    ) -> None:
        if isinstance(value, int):
            self.value = float(value)
        elif isinstance(value, str) and "date" in self.key.lower():
            try:
                dt = dateparser.parse(value)
                if dt is None:
                    self.value = value
                else:
                    self.value = dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"date error [{value}]: [{e}]")
                self.value = value
        else:
            self.value = value


ExtractedField.model_rebuild()
