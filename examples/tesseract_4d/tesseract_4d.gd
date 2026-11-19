extends Node3D
class_name MN24Tesseract4D

@export var rotation_xw := 0.40
@export var rotation_yw := 0.25
@export var rotation_zw := 0.15
@export_range(2.1, 12.0, 0.1) var projection_distance := 4.0
@export var display_scale := 2.0
@export var line_color := Color(0.12, 0.82, 1.0, 1.0)
@export var auto_rotate := true

var vertices_4d: Array[Vector4] = []
var edges: Array[Vector2i] = []
var angle_xw := 0.0
var angle_yw := 0.0
var angle_zw := 0.0

var mesh_data: ImmediateMesh
var mesh_node: MeshInstance3D
var material: StandardMaterial3D


func _ready() -> void:
    _generate_tesseract()
    _setup_renderer()
    _update_mesh()


func _generate_tesseract() -> void:
    vertices_4d.clear()
    edges.clear()

    for i in range(16):
        vertices_4d.append(Vector4(
            1.0 if (i & 1) else -1.0,
            1.0 if (i & 2) else -1.0,
            1.0 if (i & 4) else -1.0,
            1.0 if (i & 8) else -1.0
        ))

    # Each edge joins vertices differing in exactly one coordinate.
    for i in range(16):
        for axis in range(4):
            var bit := 1 << axis
            if (i & bit) == 0:
                edges.append(Vector2i(i, i | bit))


func _setup_renderer() -> void:
    mesh_data = ImmediateMesh.new()
    mesh_node = MeshInstance3D.new()
    mesh_node.name = "TesseractWireframe"
    mesh_node.mesh = mesh_data
    add_child(mesh_node)

    material = StandardMaterial3D.new()
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    material.albedo_color = line_color
    material.emission_enabled = true
    material.emission = line_color


func _rotate_xw(p: Vector4, a: float) -> Vector4:
    var c := cos(a)
    var s := sin(a)
    return Vector4(p.x * c - p.w * s, p.y, p.z, p.x * s + p.w * c)


func _rotate_yw(p: Vector4, a: float) -> Vector4:
    var c := cos(a)
    var s := sin(a)
    return Vector4(p.x, p.y * c - p.w * s, p.z, p.y * s + p.w * c)


func _rotate_zw(p: Vector4, a: float) -> Vector4:
    var c := cos(a)
    var s := sin(a)
    return Vector4(p.x, p.y, p.z * c - p.w * s, p.z * s + p.w * c)


func project_to_3d(p: Vector4) -> Vector3:
    var denominator := projection_distance - p.w
    if absf(denominator) < 0.001:
        denominator = 0.001
    var factor := projection_distance / denominator
    return Vector3(p.x, p.y, p.z) * factor * display_scale


func _update_mesh() -> void:
    var projected: Array[Vector3] = []
    for vertex in vertices_4d:
        var rotated := _rotate_xw(vertex, angle_xw)
        rotated = _rotate_yw(rotated, angle_yw)
        rotated = _rotate_zw(rotated, angle_zw)
        projected.append(project_to_3d(rotated))

    mesh_data.clear_surfaces()
    mesh_data.surface_begin(Mesh.PRIMITIVE_LINES, material)
    for edge in edges:
        mesh_data.surface_add_vertex(projected[edge.x])
        mesh_data.surface_add_vertex(projected[edge.y])
    mesh_data.surface_end()


func _process(delta: float) -> void:
    if auto_rotate:
        angle_xw += delta * rotation_xw
        angle_yw += delta * rotation_yw
        angle_zw += delta * rotation_zw
    _update_mesh()


func reset_rotation() -> void:
    angle_xw = 0.0
    angle_yw = 0.0
    angle_zw = 0.0
    _update_mesh()
