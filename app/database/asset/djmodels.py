from ..base import DataJson

class AccountExtraInfo(DataJson):
    __datajson_id__ = 'account_extra_info'

    IBAN: str | None = 'IBAN'

    key_info = {
        'data': (
            'IBAN',
        )
    }

    def validate(self) -> bool:
        if self.IBAN and len(self.IBAN) != 22:
            raise ValueError("IBAN must be 22 characters long.")
        return True

class ManagerExtraInfo(DataJson):
    __datajson_id__ = 'manager_extra_info'

    remarks: str | None = 'text'

    key_info = {
        'data': (
            'remarks',
        )
    }

    def validate(self) -> bool:
        return True
    
class OrganizationExtraInfo(DataJson):
    __datajson_id__ = 'organization_extra_info'

    remarks: str | None = 'text'

    key_info = {
        'data': (
            'remarks',
        )
    }

    def validate(self) -> bool:
        return True