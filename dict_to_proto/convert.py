"""
    Set of function to help us convert a python dictionary into a protobuff
"""

from typing import Dict, TypeVar, List, Union, Callable

from diplomacy_research.proto.diplomacy_proto.game_pb2 import Message, PhaseHistory, State, SavedGame
from diplomacy_research.proto.diplomacy_proto.common_pb2 import MapStringList
from diplomacy_research.proto.tensorflow_serving.apis.model_management_pb2 import ReloadConfigRequest
from diplomacy_research.proto.tensorflow_serving.config.model_server_config_pb2 import ModelConfig

ProtoBuff = TypeVar('ProtoBuff')


# pylint: disable=unused-argument
def set_nothing(proto: ProtoBuff, name: str, value: any) -> None:
    """ dummy function since ProtoBuff is imperative and mutate the protobuff inplace"""
    # pylint: disable=unnecessary-pass
    pass


def make_map_list(pdict: Dict[str, List[any]], proto: ProtoBuff) -> ProtoBuff:
    """ Insert a python dictionary into a protocol buffer message """

    for name, value in pdict.items():
        proto[name].value.extend(value)

    return proto


def make_map_value(pdict: Dict[str, any], proto: ProtoBuff) -> None:
    """ Insert a python dictionary into a protocol buffer message """
    for name, value in pdict.items():
        proto[name] = value


def make_builds(pdict: Dict[str, Dict[str, any]], proto: ProtoBuff) -> None:
    """ Insert a python dictionary into a `builds` protocol buffer message """

    for key, value in pdict.items():
        if value is None:
            continue

        proto[key].count = value['count']
        proto[key].homes.extend(value['homes'])


def make_policy(pdict: Dict[str, Dict[str, List[any]]], proto: ProtoBuff) -> None:
    """ Insert a python dictionary into a `policy` protocol buffer message """

    for key, value in pdict.items():
        if value is None:
            continue

        proto[key].locs.extend(value['locs'])
        proto[key].tokens.extend(value['tokens'])
        proto[key].log_probs.extend(value['log_probs'])


def make_kwargs(pdict, proto: ProtoBuff) -> None:
    """ Insert a python dictionary into a `kawargs` protocol buffer message """
    for key, value in pdict.items():
        if value is None:
            continue

        proto[key].player_seed = value['player_seed']
        proto[key].noise = value['noise']
        proto[key].temperature = value['temperature']
        proto[key].dropout_rate = value['dropout_rate']


def make_model_config(value):
    """ create a model config proto from a dictionary"""
    proto = ModelConfig()
    proto.name = value['name']
    proto.base_path = value['base_path']
    proto.model_platform = value['model_platform']
    return proto


def forward_make_proto(pdict: Dict[str, any], proto: ProtoBuff) -> ProtoBuff:
    """ forward reference to convert_to_proto """
    return convert_to_proto(pdict, proto)


def make_message(pdict: Dict[str, any], _: ProtoBuff) -> ProtoBuff:
    """ forward reference to convert_to_proto with Message """
    return convert_to_proto(pdict, Message)


def make_messages(pdict: List[Dict[str, any]], _) -> List[ProtoBuff]:
    """ Transform a list of messages into a list of protobuff messages"""
    return [convert_to_proto(item, Message) for item in pdict]


def make_phases(pdict: List[Dict[str, any]], _) -> List[ProtoBuff]:
    """ Transform a list of history dict into a list of protobuff PhaseHistory"""
    return [convert_to_proto(item, PhaseHistory) for item in pdict]


# define how to process each fields
__dispatcher__ = {
    'state': forward_make_proto,
    'phase': forward_make_proto,
    'phases': make_phases,
    'units': make_map_list,
    'centers': make_map_list,
    'orders': make_map_list,
    'homes': make_map_list,
    'builds': make_builds,
    'context': make_map_list,
    'results': make_map_list,
    'message': make_message,
    'messages': make_messages,
    'policy': make_policy,
    'state_value': make_map_value,
    'possible_orders': make_map_list,
    'civil_disorder': make_map_value,
    'influence': make_map_list,
    'rewards': make_map_list,
    'returns': make_map_list,
    'kwargs': make_kwargs,
    'config': make_map_list,
}


def extend(proto: ProtoBuff, name: str, value: List[any]):
    """ extend protocol buffer value (set for arrays)"""
    return getattr(proto, name).extend(value)


# define how to set a value
__setter_table__ = {
    'rules': extend,
    'messages': extend,
    'phases': extend,
    'board_state': extend,
    'prev_orders_state': extend,
    'units': set_nothing,
    'centers': set_nothing,
    'homes': set_nothing,
    'builds': set_nothing,
    'context': set_nothing,
    'state': set_nothing,
    'orders': set_nothing,
    'results': set_nothing,
    'policy': set_nothing,
    'state_value': set_nothing,
    'possible_orders': set_nothing,
    'tokens': extend,
    'civil_disorder': set_nothing,
    'influence': set_nothing,

    # pylint: disable=fixme
    # FIXME Those fields from SavedGame are not unit tested
    'assigned_powers': extend,
    'players': extend,
    'kwargs': set_nothing,
    'rewards': set_nothing,
    'returns': set_nothing,
    'config': set_nothing
}


def make_reload_config_request(pdict: Dict[str, any]) -> ProtoBuff:
    """ Specialization for the config request proto """

    model_configs = [make_model_config(item) for item in pdict['config']['model_config_list']['config']]

    proto = ReloadConfigRequest()

    # pylint: disable=no-member
    proto.config.model_config_list.config.extend(model_configs)

    return proto


def convert_to_proto(pdict: Dict[str, any], proto_constructor: Union[ProtoBuff, Callable],
                     strict: bool = False) -> ProtoBuff:
    """ instantiate a protobuff using a python dictionary
        `proto_constructor` can be a protobuff constructor or a reference to an existing protobuff field
    """
    proto = proto_constructor

    if proto_constructor is ReloadConfigRequest:
        return make_reload_config_request(pdict)

    if proto_constructor is MapStringList:
        return make_map_list(pdict, MapStringList().value)

    # timestamp is not in protobuff
    if not strict and 'timestamp' in pdict:
        pdict.pop('timestamp')

    if callable(proto_constructor):
        proto = proto_constructor()

    for name, value in pdict.items():
        try:
            setter = __setter_table__.get(name, setattr)

            if name in __dispatcher__ and not isinstance(value, str):
                value = __dispatcher__[name](value, getattr(proto, name))

            setter(proto, name, value)
        except Exception as exception:
            print('exception: {}'.format(exception))
            print('name: {}'.format(name))
            print('value: {}'.format(value))
            print('proto: {}'.format(proto))
            raise exception

    return proto


def convert_message(pdict: Dict[str, any]) -> ProtoBuff:
    """ Specialization of `convert_to_proto` for Message """
    return convert_to_proto(pdict, Message)


def convert_phase_history(pdict: Dict[str, any]) -> ProtoBuff:
    """ Specialization of `convert_to_proto` for PhaseHistory """
    return convert_to_proto(pdict, PhaseHistory)


def convert_state(pdict: Dict[str, any]) -> ProtoBuff:
    """ Specialization of `convert_to_proto` for StateProto """
    return convert_to_proto(pdict, State)


def convert_saved_game(pdict: Dict[str, any]) -> ProtoBuff:
    """ Specialization of `convert_to_proto` for SavedGame """
    return convert_to_proto(pdict, SavedGame)
