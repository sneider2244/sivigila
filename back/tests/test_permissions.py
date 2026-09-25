from app.domain.enums import Rol
from app.domain.permissions import puede_gestionar, permisos_por_defecto, roles_asignables


def test_super_admin_gestiona_a_todos():
    permisos = permisos_por_defecto(Rol.SUPER_ADMIN)
    assert puede_gestionar(Rol.SUPER_ADMIN, permisos, Rol.ADMIN)
    assert puede_gestionar(Rol.SUPER_ADMIN, permisos, Rol.SUPER_ADMIN)


def test_admin_no_gestiona_a_otro_admin():
    permisos = permisos_por_defecto(Rol.ADMIN)
    assert puede_gestionar(Rol.ADMIN, permisos, Rol.DIGITADOR)
    assert not puede_gestionar(Rol.ADMIN, permisos, Rol.ADMIN)


def test_consulta_no_gestiona():
    permisos = permisos_por_defecto(Rol.CONSULTA)
    assert not puede_gestionar(Rol.CONSULTA, permisos, Rol.CONSULTA)


def test_roles_asignables_admin_excluye_super_admin():
    asignables = roles_asignables(Rol.ADMIN)
    assert Rol.SUPER_ADMIN not in asignables
    assert Rol.DIGITADOR in asignables
