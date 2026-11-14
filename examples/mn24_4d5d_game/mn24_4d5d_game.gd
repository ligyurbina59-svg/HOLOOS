extends Node3D
class_name MN24FourDFiveDGame

## Playable 4D/5D hypercube exploration prototype.
## 4D = tesseract (16 vertices, 32 edges); 5D = penteract (32 vertices, 80 edges).

@export_range(4, 5, 1) var initial_dimension := 4
@export var rotation_speed := 0.55
@export var movement_speed := 5.0
@export var projection_distance := 4.5
@export var world_scale := 2.2

var dimension := 4
var vertices: Array[PackedFloat32Array] = []
var edges: Array[Vector2i] = []
var angles: Dictionary = {}
var player_position := Vector3.ZERO
var collected := 0
var core_positions: Array[Vector3] = []
var core_nodes: Array[MeshInstance3D] = []
var mesh_data: ImmediateMesh
var wire_node: MeshInstance3D
var core_material: StandardMaterial3D
var player_node: MeshInstance3D
var hud: Label
var status: Label
var rotating := true

const ROTATION_PLANES := [[0, 3], [1, 3], [2, 3], [0, 4], [1, 4], [2, 4], [3, 4]]

func _ready() -> void:
    dimension = clampi(initial_dimension, 4, 5)
    _setup_scene()
    _build_hypercube()
    _rebuild_core_nodes()
    _update_geometry()
    _update_hud()

func _setup_scene() -> void:
    var environment := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.012, 0.022, 0.055)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.28, 0.42, 0.62)
    env.ambient_light_energy = 0.8
    environment.environment = env
    add_child(environment)

    mesh_data = ImmediateMesh.new()
    wire_node = MeshInstance3D.new()
    wire_node.name = "HyperCubeWireframe"
    wire_node.mesh = mesh_data
    add_child(wire_node)
    var wire_material := StandardMaterial3D.new()
    wire_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    wire_material.albedo_color = Color(0.12, 0.82, 1.0)
    wire_material.emission_enabled = true
    wire_material.emission = Color(0.05, 0.55, 1.0)
    wire_node.material_override = wire_material

    core_material = StandardMaterial3D.new()
    core_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    core_material.albedo_color = Color(1.0, 0.68, 0.12)
    core_material.emission_enabled = true
    core_material.emission = Color(1.0, 0.32, 0.04)

    var player_mesh := SphereMesh.new()
    player_mesh.radius = 0.22
    player_mesh.height = 0.44
    player_node = MeshInstance3D.new()
    player_node.name = "Explorer"
    player_node.mesh = player_mesh
    var player_mat := StandardMaterial3D.new()
    player_mat.albedo_color = Color(0.25, 1.0, 0.52)
    player_mat.emission_enabled = true
    player_mat.emission = Color(0.08, 0.8, 0.22)
    player_node.material_override = player_mat
    add_child(player_node)

    var layer := CanvasLayer.new()
    add_child(layer)
    hud = Label.new()
    hud.position = Vector2(22, 18)
    hud.add_theme_font_size_override("font_size", 20)
    hud.add_theme_color_override("font_color", Color(0.78, 0.94, 1.0))
    layer.add_child(hud)
    status = Label.new()
    status.position = Vector2(22, 118)
    status.add_theme_font_size_override("font_size", 15)
    status.add_theme_color_override("font_color", Color(1.0, 0.78, 0.36))
    layer.add_child(status)

func _build_hypercube() -> void:
    vertices.clear()
    edges.clear()
    angles.clear()
    var count := 1 << dimension
    for i in range(count):
        var point := PackedFloat32Array()
        for axis in range(dimension):
            point.append(1.0 if (i & (1 << axis)) != 0 else -1.0)
        vertices.append(point)
    for i in range(count):
        for axis in range(dimension):
            var bit := 1 << axis
            if (i & bit) == 0:
                edges.append(Vector2i(i, i | bit))
    for plane in ROTATION_PLANES:
        if plane[1] < dimension:
            angles[str(plane[0]) + ":" + str(plane[1])] = 0.0

func _rotate_plane(point: PackedFloat32Array, axis_a: int, axis_b: int, angle: float) -> PackedFloat32Array:
    var result := point.duplicate()
    var c := cos(angle)
    var s := sin(angle)
    var a := point[axis_a]
    var b := point[axis_b]
    result[axis_a] = a * c - b * s
    result[axis_b] = a * s + b * c
    return result

func _project_to_3d(point: PackedFloat32Array) -> Vector3:
    var p := point.duplicate()
    if dimension == 5:
        var d5 := maxf(0.15, projection_distance - p[4])
        var factor5 := projection_distance / d5
        for axis in range(4):
            p[axis] *= factor5
    var d4 := maxf(0.15, projection_distance - p[3])
    var factor4 := projection_distance / d4
    return Vector3(p[0], p[1], p[2]) * factor4 * world_scale

func _project_all() -> Array[Vector3]:
    var projected: Array[Vector3] = []
    for source in vertices:
        var point := source.duplicate()
        for plane in ROTATION_PLANES:
            if plane[1] < dimension:
                var key := str(plane[0]) + ":" + str(plane[1])
                point = _rotate_plane(point, plane[0], plane[1], float(angles.get(key, 0.0)))
        projected.append(_project_to_3d(point))
    return projected

func _rebuild_core_nodes() -> void:
    for node in core_nodes:
        node.queue_free()
    core_nodes.clear()
    core_positions.clear()
    collected = 0
    var sphere := SphereMesh.new()
    sphere.radius = 0.16
    sphere.height = 0.32
    for i in range(3):
        var marker := MeshInstance3D.new()
        marker.name = "EnergyCore" + str(i + 1)
        marker.mesh = sphere
        marker.material_override = core_material
        add_child(marker)
        core_nodes.append(marker)
        core_positions.append(Vector3.ZERO)

func _update_geometry() -> void:
    var projected := _project_all()
    mesh_data.clear_surfaces()
    mesh_data.surface_begin(Mesh.PRIMITIVE_LINES)
    for edge in edges:
        mesh_data.surface_add_vertex(projected[edge.x])
        mesh_data.surface_add_vertex(projected[edge.y])
    mesh_data.surface_end()
    var chosen := [1, min(1 << (dimension - 1), vertices.size() - 1), vertices.size() - 2]
    for i in range(core_nodes.size()):
        core_positions[i] = projected[chosen[i]]
        core_nodes[i].position = core_positions[i]
        core_nodes[i].visible = i >= collected
    player_node.position = player_position

func _process(delta: float) -> void:
    if rotating:
        for key in angles.keys():
            angles[key] = float(angles[key]) + delta * rotation_speed * (1.0 + float(int(key.replace(":", "")) % 3) * 0.12)
    _move_player(delta)
    _update_geometry()

func _move_player(delta: float) -> void:
    var direction := Vector3.ZERO
    if Input.is_key_pressed(KEY_W): direction.z -= 1.0
    if Input.is_key_pressed(KEY_S): direction.z += 1.0
    if Input.is_key_pressed(KEY_A): direction.x -= 1.0
    if Input.is_key_pressed(KEY_D): direction.x += 1.0
    if Input.is_key_pressed(KEY_SPACE): direction.y += 1.0
    if Input.is_key_pressed(KEY_C): direction.y -= 1.0
    if direction.length_squared() > 0.0:
        player_position += direction.normalized() * movement_speed * delta
    player_position.x = clampf(player_position.x, -8.0, 8.0)
    player_position.y = clampf(player_position.y, -8.0, 8.0)
    player_position.z = clampf(player_position.z, -8.0, 8.0)

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        match event.keycode:
            KEY_4:
                _set_dimension(4)
            KEY_5:
                _set_dimension(5)
            KEY_R:
                rotating = not rotating
            KEY_E:
                _collect_nearby_core()
            KEY_HOME:
                player_position = Vector3.ZERO
                _update_geometry()

func _set_dimension(value: int) -> void:
    if value == dimension:
        return
    dimension = clampi(value, 4, 5)
    _build_hypercube()
    _rebuild_core_nodes()
    _update_geometry()
    _update_hud()

func _collect_nearby_core() -> void:
    if collected >= core_nodes.size():
        status.text = "¡Misión completada! Has reunido los 3 núcleos. Pulsa 4 o 5 para explorar otra dimensión."
        return
    var target := core_positions[collected]
    if player_position.distance_to(target) <= 1.35:
        collected += 1
        status.text = "Núcleo recogido: " + str(collected) + "/3"
        if collected == 3:
            status.text = "¡Misión completada! Has reunido los 3 núcleos."
    else:
        status.text = "Acércate al núcleo brillante y pulsa E. Distancia: " + str(snappedf(player_position.distance_to(target), 0.1))
    _update_geometry()
    _update_hud()

func _update_hud() -> void:
    var vertex_count := 1 << dimension
    var edge_count := dimension * (1 << (dimension - 1))
    hud.text = "MN24 4D/5D EXPLORER  |  DIMENSIÓN: " + str(dimension) + "D\nVértices: " + str(vertex_count) + "  |  Aristas: " + str(edge_count) + "  |  Núcleos: " + str(collected) + "/3\nWASD mover · ESPACIO/CTRL subir/bajar · E recoger · R rotación · 4/5 cambiar dimensión · HOME reiniciar"
