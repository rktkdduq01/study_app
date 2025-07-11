from typing import List, Optional, Dict, Any
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.api.deps import get_current_active_user


class Permission(str, Enum):
    """System permissions"""
    # User permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Character permissions
    CHARACTER_CREATE = "character:create"
    CHARACTER_READ = "character:read"
    CHARACTER_UPDATE = "character:update"
    CHARACTER_DELETE = "character:delete"
    
    # Quest permissions
    QUEST_CREATE = "quest:create"
    QUEST_READ = "quest:read"
    QUEST_UPDATE = "quest:update"
    QUEST_DELETE = "quest:delete"
    QUEST_ASSIGN = "quest:assign"
    
    # Achievement permissions
    ACHIEVEMENT_CREATE = "achievement:create"
    ACHIEVEMENT_READ = "achievement:read"
    ACHIEVEMENT_UPDATE = "achievement:update"
    ACHIEVEMENT_DELETE = "achievement:delete"
    ACHIEVEMENT_GRANT = "achievement:grant"
    
    # Content permissions
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"
    
    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_MANAGE_CONTENT = "admin:manage_content"
    ADMIN_VIEW_ALL = "admin:view_all"


# Role-Permission mappings
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.CHILD: [
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.CHARACTER_CREATE,
        Permission.CHARACTER_READ,
        Permission.CHARACTER_UPDATE,
        Permission.QUEST_READ,
        Permission.ACHIEVEMENT_READ,
        Permission.CONTENT_READ,
    ],
    
    UserRole.PARENT: [
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.CHARACTER_READ,
        Permission.QUEST_READ,
        Permission.ACHIEVEMENT_READ,
        Permission.CONTENT_READ,
        Permission.ANALYTICS_READ,
    ],
    
    UserRole.TEACHER: [
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.CHARACTER_READ,
        Permission.QUEST_CREATE,
        Permission.QUEST_READ,
        Permission.QUEST_UPDATE,
        Permission.QUEST_ASSIGN,
        Permission.ACHIEVEMENT_READ,
        Permission.ACHIEVEMENT_GRANT,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_EXPORT,
    ],
    
    UserRole.ADMIN: [
        # Admin has all permissions
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.CHARACTER_CREATE,
        Permission.CHARACTER_READ,
        Permission.CHARACTER_UPDATE,
        Permission.CHARACTER_DELETE,
        Permission.QUEST_CREATE,
        Permission.QUEST_READ,
        Permission.QUEST_UPDATE,
        Permission.QUEST_DELETE,
        Permission.QUEST_ASSIGN,
        Permission.ACHIEVEMENT_CREATE,
        Permission.ACHIEVEMENT_READ,
        Permission.ACHIEVEMENT_UPDATE,
        Permission.ACHIEVEMENT_DELETE,
        Permission.ACHIEVEMENT_GRANT,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_EXPORT,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_MANAGE_USERS,
        Permission.ADMIN_MANAGE_CONTENT,
        Permission.ADMIN_VIEW_ALL,
    ],
}


class PermissionChecker:
    """Permission checker dependency"""
    
    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """Check if user has required permissions"""
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        
        # Check if user has all required permissions
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required: {permission}"
                )
        
        return current_user


def require_permissions(permissions: List[Permission]):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permissions
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            for permission in permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Not enough permissions. Required: {permission}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has specific permission"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return any(permission in user_permissions for permission in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """Check if user has all specified permissions"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return all(permission in user_permissions for permission in permissions)


def check_resource_ownership(
    user: User,
    resource: Any,
    owner_field: str = "user_id",
    allow_admin: bool = True
) -> bool:
    """
    Check if user owns a resource or is admin.
    
    Args:
        user: Current user
        resource: Resource to check
        owner_field: Field name that contains owner ID
        allow_admin: Whether to allow admin access
    
    Returns:
        True if user owns resource or is admin
    """
    if allow_admin and user.role == UserRole.ADMIN:
        return True
    
    owner_id = getattr(resource, owner_field, None)
    return owner_id == user.id


def check_parent_child_relationship(
    parent: User,
    child: User
) -> bool:
    """Check if user is parent of child"""
    return parent.role == UserRole.PARENT and child.parent_id == parent.id


class ResourceOwnershipChecker:
    """Check resource ownership dependency"""
    
    def __init__(
        self,
        owner_field: str = "user_id",
        allow_admin: bool = True,
        allow_teacher: bool = False
    ):
        self.owner_field = owner_field
        self.allow_admin = allow_admin
        self.allow_teacher = allow_teacher
    
    def check(self, user: User, resource: Any) -> bool:
        """Check if user can access resource"""
        # Admin access
        if self.allow_admin and user.role == UserRole.ADMIN:
            return True
        
        # Teacher access
        if self.allow_teacher and user.role == UserRole.TEACHER:
            return True
        
        # Owner access
        owner_id = getattr(resource, self.owner_field, None)
        if owner_id == user.id:
            return True
        
        # Parent access to child's resources
        if user.role == UserRole.PARENT and hasattr(resource, 'user'):
            child = resource.user
            if child and child.parent_id == user.id:
                return True
        
        return False