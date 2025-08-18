from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(type="string")

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserPublic(UserBase):
    id: str = Field(..., alias="_id")
    username: str
    is_verified: bool = False

    @model_validator(mode='before')
    def convert_object_id_to_str(cls, data):
        if isinstance(data, dict) and '_id' in data:
            data['_id'] = str(data['_id'])
        return data

class EmailVerification(BaseModel):
    token: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Trait(BaseModel):
    name: str
    description: Optional[str] = None

class CharacterCreate(BaseModel):
    name: str
    physical: List[Trait]
    mental: List[Trait]
    skills: List[Trait]
    flaws: List[Trait]
    background: Optional[str] = None
    beliefs: Optional[str] = None

class CharacterPublic(CharacterCreate):
    id: str = Field(..., alias="_id")
    owner_id: str
    evaluation: Optional[str] = None

    @model_validator(mode='before')
    def convert_object_id_to_str(cls, data):
        if isinstance(data, dict) and '_id' in data:
            data['_id'] = str(data['_id'])
        return data

class CharacterEvaluation(BaseModel):
    evaluation_text: str
    suggested_corrections: 'CharacterCreate'
    needs_improvement: bool = True

class CharacterCorrectionRequest(BaseModel):
    original_character: CharacterCreate
    accept_suggestions: bool = False

class WorldCreate(BaseModel):
    title: str
    summary: str
    context: str
    logic: str
    time_period: str
    space_setting: str
    is_public: bool = False
    allow_action_suggestions: bool = True

class WorldPublic(WorldCreate):
    id: str = Field(..., alias="_id")
    creator_id: str
    created_at: Optional[str] = None
    usage_count: int = 0

    @model_validator(mode='before')
    def convert_object_id_to_str(cls, data):
        if isinstance(data, dict) and '_id' in data:
            data['_id'] = str(data['_id'])
        return data

class RoomCreate(BaseModel):
    name: str
    world_id: str
    max_chapters: int = Field(default=5, ge=1, le=20, description="Número máximo de capítulos (entre 1 y 20)")
    max_players: int = 4
    allow_suggestions: bool = True
    discussion_time: int = 300
    auto_continue: bool = False
    continue_time: int = 60

class RoomMessage(BaseModel):
    user_id: str
    username: str
    message: str
    timestamp: str
    message_type: str = "chat"

class RoomPublic(RoomCreate):
    id: str = Field(..., alias="_id")
    owner_id: str
    world: Optional[WorldPublic] = None
    created_at: Optional[str] = None
    admin_id: str
    member_ids: List[str] = []
    members: List[dict] = []  # Información completa de los miembros
    selected_characters: List[dict] = []  # Personajes seleccionados para la partida
    current_chapter: int = 0
    chapters: List[str] = []
    messages: List[RoomMessage] = []
    game_state: str = "waiting"  # "waiting", "character_selection", "playing", "discussion", "action_phase", "finished"
    current_actions: List[dict] = []  # Acciones propuestas por los jugadores
    ready_players: List[str] = []  # IDs de jugadores que están listos
    allow_actions: bool = True
    action_time_minutes: int = 5
    pending_actions: List[dict] = []

    @model_validator(mode='before')
    def convert_object_id_to_str(cls, data):
        if isinstance(data, dict) and '_id' in data:
            data['_id'] = str(data['_id'])
        if isinstance(data, dict) and 'world' in data and data['world'] and '_id' in data['world']:
             data['world']['_id'] = str(data['world']['_id'])
        return data

# Modelos para GameRoom
class GameRoomMember(BaseModel):
    id: str
    username: str
    email: str
    is_ready: bool = False
    selected_character_id: Optional[str] = None

class SelectedCharacter(BaseModel):
    id: str
    name: str
    physical: List[Trait]
    mental: List[Trait]
    skills: List[Trait]
    flaws: List[Trait]
    background: Optional[str] = None
    beliefs: Optional[str] = None
    owner_id: str
    owner_username: str

class GameRoomChatMessage(BaseModel):
    id: Optional[str] = None
    user_id: str
    username: str
    message: str
    timestamp: str
    message_type: str = "chat"  # "chat", "system", "action", "story"

class GameRoomPlayerAction(BaseModel):
    id: Optional[str] = None
    user_id: str
    username: str
    character_id: str
    character_name: str
    action: str
    timestamp: str
    status: str = "pending"  # "pending", "approved", "rejected"

class ChapterData(BaseModel):
    chapter_number: int
    content: str
    actions_included: List[GameRoomPlayerAction] = []
    timestamp: str

class GameRoom(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    world_id: str
    world: Optional[WorldPublic] = None
    admin_id: str
    member_ids: List[str] = []
    members: List[GameRoomMember] = []
    selected_characters: List[SelectedCharacter] = []
    current_chapter: int = 0
    max_chapters: int = 5
    chapters: List[str] = []
    messages: List[GameRoomChatMessage] = []
    game_state: str = "waiting"
    allow_actions: bool = True
    action_time_minutes: int = 5
    pending_actions: List[GameRoomPlayerAction] = []
    ready_players: List[str] = []
    created_at: Optional[str] = None

    @model_validator(mode='before')
    def convert_object_id_to_str(cls, data):
        if isinstance(data, dict) and '_id' in data:
            data['_id'] = str(data['_id'])
        if isinstance(data, dict) and 'world' in data and data['world'] and '_id' in data['world']:
             data['world']['_id'] = str(data['world']['_id'])
        return data

# Requests para GameRoom
class JoinGameRoomRequest(BaseModel):
    pass

class SelectCharacterRequest(BaseModel):
    character_id: str

class SetReadyRequest(BaseModel):
    ready: bool = True

class SendChatMessageRequest(BaseModel):
    message: str
    message_type: str = "chat"

class ProposeActionRequest(BaseModel):
    character_id: str
    action: str

class KickPlayerRequest(BaseModel):
    player_id: str

# Modelos legacy (mantener compatibilidad)
class ActionSuggestion(BaseModel):
    text: str

class CharacterSelection(BaseModel):
    character_id: str
    
class ChatMessage(BaseModel):
    message: str
    message_type: str = "chat"  # "chat", "action"
    
class PlayerAction(BaseModel):
    action: str
    character_id: Optional[str] = None

# (Se eliminan documentos de 'gamerooms'; el juego se normaliza con 'games' y colecciones 'game_*')

# ================= Normalized Game Collections (Mongo) =================

class GameSettings(BaseModel):
    allow_suggestions: bool = True
    discussion_time: int = 300  # seconds
    auto_continue: bool = False
    continue_time: int = 60  # seconds

class GameMeta(BaseModel):
    id: str = Field(..., alias="_id")
    room_id: str
    name: str
    world_id: str
    max_chapters: int = 5
    max_players: int = 4
    settings: GameSettings
    owner_id: str
    admin_id: str
    current_chapter: int = 0
    game_state: str = "playing"  # playing, discussion, finished
    created_at: Optional[str] = None
    current_deadline: Optional[str] = None

    @model_validator(mode='before')
    def _normalize_ids(cls, data):
        if isinstance(data, dict):
            if '_id' in data:
                data['_id'] = str(data['_id'])
            for key in ['room_id', 'world_id', 'owner_id', 'admin_id']:
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
        return data

class GameMemberDoc(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    game_id: str
    user_id: str
    character_id: Optional[str] = None
    role: str = "player"  # player | admin
    joined_at: Optional[str] = None
    is_ready: bool = False

    @model_validator(mode='before')
    def _normalize_ids(cls, data):
        if isinstance(data, dict):
            if '_id' in data and data['_id'] is not None:
                data['_id'] = str(data['_id'])
            for key in ['game_id', 'user_id', 'character_id']:
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
        return data

class GameChapterDoc(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    game_id: str
    chapter_number: int
    content: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    @model_validator(mode='before')
    def _normalize_ids(cls, data):
        if isinstance(data, dict):
            if '_id' in data and data['_id'] is not None:
                data['_id'] = str(data['_id'])
            for key in ['game_id', 'created_by']:
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
        return data

class GameMessageDoc(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    game_id: str
    chapter_id: Optional[str] = None
    user_id: str
    content: str
    type: str = "chat"  # chat | system | action
    timestamp: Optional[str] = None

    @model_validator(mode='before')
    def _normalize_ids(cls, data):
        if isinstance(data, dict):
            if '_id' in data and data['_id'] is not None:
                data['_id'] = str(data['_id'])
            for key in ['game_id', 'chapter_id', 'user_id']:
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
        return data

class GameActionDoc(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    game_id: str
    user_id: str
    character_id: Optional[str] = None
    action: str
    status: str = "pending"  # pending | approved | rejected
    created_at: Optional[str] = None
    chapter_id: Optional[str] = None

    @model_validator(mode='before')
    def _normalize_ids(cls, data):
        if isinstance(data, dict):
            if '_id' in data and data['_id'] is not None:
                data['_id'] = str(data['_id'])
            for key in ['game_id', 'user_id', 'character_id', 'chapter_id']:
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
        return data
