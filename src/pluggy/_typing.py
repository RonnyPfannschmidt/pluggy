from typing import Optional, Union, Dict

from typing_extensions import TypedDict, Final


class HookSpecMarkerData:
    firstresult: Final[bool]
    historic: Final[bool]
    warn_on_impl: Final[Optional[Warning]]

    def __init__(
        self,
        firstresult: bool = False,
        historic: bool = False,
        warn_on_impl: Optional[Warning] = None,
    ):
        self.firstresult = firstresult
        self.historic = historic
        self.warn_on_impl = warn_on_impl

    @staticmethod
    def from_parse(
        parse: Union[
            Dict[str, Union[bool, str, Optional[Warning], None]], "HookSpecMarkerData"
        ]
    ) -> "HookSpecMarkerData":
        if isinstance(parse, HookSpecMarkerData):
            return parse
        else:
            return HookSpecMarkerData(**parse)  # type: ignore


class HookImplMarkerData:
    hookwrapper: Final[bool]
    optionalhook: Final[bool]
    tryfirst: Final[bool]
    trylast: Final[bool]
    specname: Final[Optional[str]]

    @staticmethod
    def from_parse(
        parse: Union[Dict[str, Union[bool, str, None]], "HookImplMarkerData"]
    ) -> "HookImplMarkerData":
        if isinstance(parse, HookImplMarkerData):
            return parse
        else:
            return HookImplMarkerData(**parse)  # type: ignore

    def __init__(
        self,
        hookwrapper: bool = False,
        optionalhook: bool = False,
        tryfirst: bool = False,
        trylast: bool = False,
        specname: Optional[str] = None,
    ):
        self.hookwrapper = hookwrapper
        self.optionalhook = optionalhook
        self.tryfirst = tryfirst
        self.trylast = trylast
        self.specname = specname
