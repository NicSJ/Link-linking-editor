bl_info = {
    "name": "Light Link (Multi-Select Custom Lists with Clear Filter, Scroll & Light Linking)",
    "author": "Your Name",
    "version": (1, 6),
    "blender": (3, 0, 0),
    "description": (
        "For the first selected light, create a new light linking receiver collection "
        "(using bpy.ops.object.light_linking_receiver_collection_new) and add the selected "
        "meshes (including those from selected collections) to it using bpy.ops.object.light_linking_add. "
        "Then assign that linking group to all selected lights by storing its name in a custom property. "
        "Also provides clear buttons for filter fields and always shows a scrollable list (10 rows tall)."
    ),
    "category": "Object",
}

import bpy

# -------------------------------------------------------------------
#   Property Groups for List Items (with multi-selection support)
# -------------------------------------------------------------------

class LL_LightItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    selected: bpy.props.BoolProperty(default=False)

class LL_MeshItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    selected: bpy.props.BoolProperty(default=False)

class LL_CollectionItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    coll: bpy.props.PointerProperty(type=bpy.types.Collection)
    selected: bpy.props.BoolProperty(default=False)

# -------------------------------------------------------------------
#   Update Functions for Full List Population
# -------------------------------------------------------------------

def update_light_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_light_items}
    scene.ll_light_items.clear()
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            item = scene.ll_light_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = prev_sel.get(obj.name, False)
    scene.ll_light_index = 0 if len(scene.ll_light_items) > 0 else -1
    print("Updated Light Items:", [item.name for item in scene.ll_light_items])

def update_mesh_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_mesh_items}
    scene.ll_mesh_items.clear()
    for obj in scene.objects:
        if obj.type == 'MESH':
            item = scene.ll_mesh_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = prev_sel.get(obj.name, False)
    scene.ll_mesh_index = 0 if len(scene.ll_mesh_items) > 0 else -1
    print("Updated Mesh Items:", [item.name for item in scene.ll_mesh_items])

def update_collection_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_collection_items}
    scene.ll_collection_items.clear()
    for coll in bpy.data.collections:
        if "Light Linking for" in coll.name:
            continue  # Skip linking collections
        item = scene.ll_collection_items.add()
        item.name = coll.name
        item.coll = coll
        item.selected = prev_sel.get(coll.name, False)
    scene.ll_collection_index = 0 if len(scene.ll_collection_items) > 0 else -1
    print("Updated Collection Items:", [item.name for item in scene.ll_collection_items])

def force_redraw(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

# -------------------------------------------------------------------
#   Operator to Toggle an Item’s Selection (via checkbox in UIList)
# -------------------------------------------------------------------

class LL_OT_ToggleSelection(bpy.types.Operator):
    bl_idname = "light_link.toggle_selection"
    bl_label = "Toggle Selection"
    bl_description = "Toggle the selection state for this item"
    
    item_name: bpy.props.StringProperty()
    item_type: bpy.props.EnumProperty(
        items=[
            ('LIGHT', "Light", ""),
            ('MESH', "Mesh", ""),
            ('COLLECTION', "Collection", ""),
        ]
    )
    
    def execute(self, context):
        scene = context.scene
        if self.item_type == 'LIGHT':
            for item in scene.ll_light_items:
                if item.name == self.item_name:
                    item.selected = not item.selected
                    break
        elif self.item_type == 'MESH':
            for item in scene.ll_mesh_items:
                if item.name == self.item_name:
                    item.selected = not item.selected
                    break
        elif self.item_type == 'COLLECTION':
            for item in scene.ll_collection_items:
                if item.name == self.item_name:
                    item.selected = not item.selected
                    break
        else:
            self.report({'WARNING'}, "Unknown item type")
            return {'CANCELLED'}
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operator to Refresh Selected Items (existing ones)
# -------------------------------------------------------------------

class LL_OT_RefreshSelectedLights(bpy.types.Operator):
    bl_idname = "light_link.refresh_selected_lights"
    bl_label = "Refresh Selected Lights"
    bl_description = (
        "Filter the lights list to show only lights selected in the viewport. "
        "If none are selected, the active light is used."
    )
    
    def execute(self, context):
        scene = context.scene
        selected_lights = [obj for obj in context.selected_objects if obj.type == 'LIGHT']
        if not selected_lights:
            active_obj = context.view_layer.objects.active
            if active_obj and active_obj.type == 'LIGHT':
                selected_lights.append(active_obj)
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected in the viewport")
            return {'CANCELLED'}
        
        scene.ll_light_items.clear()
        for obj in selected_lights:
            item = scene.ll_light_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = True
        scene.ll_light_index = 0 if len(scene.ll_light_items) > 0 else -1
        
        force_redraw(context)
        self.report({'INFO'}, f"Filtered lights list to {len(selected_lights)} item(s)")
        return {'FINISHED'}

class LL_OT_RefreshSelectedMeshes(bpy.types.Operator):
    bl_idname = "light_link.refresh_selected_meshes"
    bl_label = "Refresh Selected Meshes"
    bl_description = (
        "Filter the mesh list to show only meshes selected in the viewport. "
        "If none are selected, the active mesh is used."
    )
    
    def execute(self, context):
        scene = context.scene
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            active_obj = context.view_layer.objects.active
            if active_obj and active_obj.type == 'MESH':
                selected_meshes.append(active_obj)
        if not selected_meshes:
            self.report({'WARNING'}, "No meshes selected in the viewport")
            return {'CANCELLED'}
        
        scene.ll_mesh_items.clear()
        for obj in selected_meshes:
            item = scene.ll_mesh_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = True
        scene.ll_mesh_index = 0 if len(scene.ll_mesh_items) > 0 else -1
        
        force_redraw(context)
        self.report({'INFO'}, f"Filtered mesh list to {len(selected_meshes)} item(s)")
        return {'FINISHED'}

class LL_OT_RefreshSelectedCollections(bpy.types.Operator):
    bl_idname = "light_link.refresh_selected_collections"
    bl_label = "Refresh Selected Collections"
    bl_description = (
        "Filter the collection list to show only collections that are selected in the Outliner. "
        "If no outliner selection is available, the UI list checkboxes (or the active collection) are used as a fallback."
    )
    
    def execute(self, context):
        scene = context.scene
        selected_collections = []
        
        # Try to get outliner selection (available in Blender 3.6+)
        if hasattr(context, "selected_ids"):
            print("Selected IDs:", context.selected_ids)
            for id_item in context.selected_ids:
                if isinstance(id_item, bpy.types.Collection):
                    selected_collections.append(id_item)
                    print("Selected Collection:", id_item.name)
        
        # Fallback: use our UI list checkboxes if no outliner selection was found.
        if not selected_collections:
            print("Using UI list checkboxes as fallback")
            selected_collections = [item.coll for item in scene.ll_collection_items if item.selected and item.coll]
            print("Selected Collections from UI List:", [coll.name for coll in selected_collections])
        
        # Second fallback: use the active UI list collection if still empty.
        if not selected_collections and scene.ll_collection_index >= 0:
            print("Using active UI list collection as fallback")
            active_item = scene.ll_collection_items[scene.ll_collection_index]
            if active_item.coll:
                selected_collections.append(active_item.coll)
                print("Active Collection:", active_item.coll.name)
        
        if not selected_collections:
            self.report({'WARNING'}, "No collections selected")
            return {'CANCELLED'}
        
        scene.ll_collection_items.clear()
        for coll in selected_collections:
            item = scene.ll_collection_items.add()
            item.name = coll.name
            item.coll = coll
            item.selected = True
        scene.ll_collection_index = 0 if len(scene.ll_collection_items) > 0 else -1
        
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        self.report({'INFO'}, f"Filtered collection list to {len(selected_collections)} item(s)")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   New Operators for “All” and “Reset” Per-List Buttons
# -------------------------------------------------------------------

class LL_OT_RefreshAllLights(bpy.types.Operator):
    bl_idname = "light_link.refresh_all_lights"
    bl_label = "Refresh All Lights"
    bl_description = "Display all lights in the scene"
    
    def execute(self, context):
        scene = context.scene
        update_light_items(scene, context)
        force_redraw(context)
        self.report({'INFO'}, f"Listed all {len(scene.ll_light_items)} lights")
        return {'FINISHED'}

class LL_OT_ResetLights(bpy.types.Operator):
    bl_idname = "light_link.reset_lights"
    bl_label = "Reset Lights"
    bl_description = "Deselect all lights in the list"
    
    def execute(self, context):
        scene = context.scene
        for item in scene.ll_light_items:
            item.selected = False
        force_redraw(context)
        self.report({'INFO'}, "Light selections reset")
        return {'FINISHED'}

class LL_OT_RefreshAllMeshes(bpy.types.Operator):
    bl_idname = "light_link.refresh_all_meshes"
    bl_label = "Refresh All Meshes"
    bl_description = "Display all meshes in the scene"
    
    def execute(self, context):
        scene = context.scene
        update_mesh_items(scene, context)
        force_redraw(context)
        self.report({'INFO'}, f"Listed all {len(scene.ll_mesh_items)} meshes")
        return {'FINISHED'}

class LL_OT_ResetMeshes(bpy.types.Operator):
    bl_idname = "light_link.reset_meshes"
    bl_label = "Reset Meshes"
    bl_description = "Deselect all meshes in the list"
    
    def execute(self, context):
        scene = context.scene
        for item in scene.ll_mesh_items:
            item.selected = False
        force_redraw(context)
        self.report({'INFO'}, "Mesh selections reset")
        return {'FINISHED'}

class LL_OT_ResetCollections(bpy.types.Operator):
    bl_idname = "light_link.reset_collections"
    bl_label = "Reset Collections"
    bl_description = "Deselect all collections in the list"
    
    def execute(self, context):
        scene = context.scene
        for item in scene.ll_collection_items:
            item.selected = False
        force_redraw(context)
        self.report({'INFO'}, "Collection selections reset")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operator to Link the Selected Lights to Selected Meshes/Collections
# -------------------------------------------------------------------

class LL_OT_Link(bpy.types.Operator):
    bl_idname = "light_link.link"
    bl_label = "Link Lights to Objects"
    bl_description = (
        "For each selected light, create (or use an existing) light linking receiver collection "
        "using bpy.ops.object.light_linking_receiver_collection_new and add the selected "
        "meshes (including those from selected collections) to it using bpy.ops.object.light_linking_add. "
        "Then assign that linking group to the light by storing its name in a custom property."
    )
    
    def execute(self, context):
        scene = context.scene

        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        selected_meshes = [item.obj for item in scene.ll_mesh_items if item.selected and item.obj]
        collection_meshes = []
        for item in scene.ll_collection_items:
            if item.selected and item.coll:
                for obj in item.coll.all_objects:
                    if obj.type == 'MESH':
                        collection_meshes.append(obj)
        
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected")
            return {'CANCELLED'}
        
        all_meshes = {obj.name: obj for obj in (selected_meshes + collection_meshes)}.values()
        if not list(all_meshes):
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        total_linked_meshes = 0
        
        for light in selected_lights:
            bpy.ops.object.select_all(action='DESELECT')
            light.select_set(True)
            context.view_layer.objects.active = light

            group_name = light.get("light_linking_receiver_collection")
            if not group_name:
                group_name = f"Light Linking for {light.name}"
            
            print("Predicted Light Linking Collection Name for", light.name, ":", group_name)
            
            new_group = bpy.data.collections.get(group_name)
            if not new_group:
                try:
                    bpy.ops.object.light_linking_receiver_collection_new()
                    group_name = light.get("light_linking_receiver_collection")
                    if not group_name:
                        group_name = f"Light Linking for {light.name}"
                        light["light_linking_receiver_collection"] = group_name
                    new_group = bpy.data.collections.get(group_name)
                    if not new_group:
                        self.report({'WARNING'}, f"Failed to find or create linking group '{group_name}' for {light.name}")
                        continue
                    print("Created Light Linking Collection for", light.name, ":", group_name)
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to create linking receiver collection for {light.name}: {str(e)}")
                    continue
            else:
                print("Using Existing Light Linking Collection for", light.name, ":", group_name)
            
            linked_meshes = 0
            for obj in all_meshes:
                if obj.name not in new_group.objects:
                    new_group.objects.link(obj)
                    linked_meshes += 1
                    print(f"Added {obj.name} to linking collection '{group_name}' for {light.name}")
                else:
                    print(f"{obj.name} already in linking collection for {light.name}")
            
            light["light_linking_receiver_collection"] = group_name
            total_linked_meshes += linked_meshes
        
        self.report({'INFO'}, f"Linked {len(selected_lights)} light(s) to {total_linked_meshes} mesh(es)")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operator to Unlink the Selected Lights from Mesh/Collection Objects
# -------------------------------------------------------------------

class LL_OT_Unlink(bpy.types.Operator):
    bl_idname = "light_link.unlink"
    bl_label = "Unlink Lights from Objects"
    bl_description = (
        "For each selected light, remove the objects (from the Mesh and Collection lists) "
        "that are linked via the light linking receiver collection and clear the linking property."
    )
    
    def execute(self, context):
        scene = context.scene
        
        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected")
            return {'CANCELLED'}
        
        total_removed = 0
        total_unlinked = 0
        
        selected_mesh_objs = [item.obj for item in scene.ll_mesh_items if item.selected and item.obj]
        selected_coll_objs = []
        for item in scene.ll_collection_items:
            if item.selected and item.coll:
                selected_coll_objs.extend([obj for obj in item.coll.all_objects if obj.type == 'MESH'])
        
        all_objs_to_unlink = set(selected_mesh_objs + selected_coll_objs)
        
        for light in selected_lights:
            group_name = light.get("light_linking_receiver_collection")
            if not group_name:
                continue
            
            linking_group = bpy.data.collections.get(group_name)
            if not linking_group:
                continue
            
            removed = 0
            for obj in all_objs_to_unlink:
                if obj.name in linking_group.objects:
                    linking_group.objects.unlink(obj)
                    removed += 1
                    print(f"Removed {obj.name} from linking group '{group_name}' for light {light.name}")
            total_removed += removed
            
            if "light_linking_receiver_collection" in light:
                del light["light_linking_receiver_collection"]
                total_unlinked += 1
        
        self.report({'INFO'}, f"Unlinked {total_unlinked} light(s) and removed {total_removed} object(s) from linking groups.")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   UIList Classes for Scrollable Lists (10 rows tall)
# -------------------------------------------------------------------

class LL_UL_LightList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "selected", text="")  # Checkbox for selection
        row.label(text=item.name)

class LL_UL_MeshList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "selected", text="")
        row.label(text=item.name)

class LL_UL_CollectionList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "selected", text="")
        row.label(text=item.name)

# -------------------------------------------------------------------
#   Panel – Three Columns in the N-Panel with plain columns (matching UI BG)
# -------------------------------------------------------------------

class LL_PT_Panel(bpy.types.Panel):
    bl_label = "Light Link"
    bl_idname = "LL_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Light Link"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        main_row = layout.row(align=True)
        
        # Lights Column
        col_lights = main_row.column(align=True)
        col_lights.label(text="Lights")
        col_lights.scale_x = 1.5
        list_col = col_lights.column(align=True)
        list_col.template_list(
            "LL_UL_LightList_UI", 
            "", 
            scene, "ll_light_items", 
            scene, "ll_light_index", 
            rows=10,
        )
        col_lights.separator()
        btn_col = col_lights.column(align=True)
        btn_col.operator("light_link.refresh_selected_lights", text="Selected Lights")
        btn_col.operator("light_link.refresh_all_lights", text="All Lights")
        btn_col.operator("light_link.reset_lights", text="Reset")
        
        # Meshes Column
        col_meshes = main_row.column(align=True)
        col_meshes.label(text="Meshes")
        col_meshes.scale_x = 1.5
        list_col = col_meshes.column(align=True)
        list_col.template_list(
            "LL_UL_MeshList_UI", 
            "", 
            scene, "ll_mesh_items", 
            scene, "ll_mesh_index", 
            rows=10,
        )
        col_meshes.separator()
        btn_col = col_meshes.column(align=True)
        btn_col.operator("light_link.refresh_selected_meshes", text="Selected Meshes")
        btn_col.operator("light_link.refresh_all_meshes", text="All Meshes")
        btn_col.operator("light_link.reset_meshes", text="Reset")
        
        # Collections Column
        col_colls = main_row.column(align=True)
        col_colls.label(text="Collections")
        col_colls.scale_x = 1.5
        list_col = col_colls.column(align=True)
        list_col.template_list(
            "LL_UL_CollectionList_UI", 
            "", 
            scene, "ll_collection_items", 
            scene, "ll_collection_index", 
            rows=10,
        )
        col_colls.separator()
        btn_col = col_colls.column(align=True)
        btn_col.label(text="")  # Placeholder (empty) for alignment (formerly "Selected Collections")
        btn_col.label(text="")  # Placeholder to match the extra row in Lights/Meshes columns
        btn_col.operator("light_link.reset_collections", text="Reset")

        
        layout.separator()
        layout.operator("light_link.link", text="Link")
        layout.operator("light_link.unlink", text="Unlink")

# -------------------------------------------------------------------
#   Registration
# -------------------------------------------------------------------

classes = (
    LL_LightItem,
    LL_MeshItem,
    LL_CollectionItem,
    LL_OT_ToggleSelection,
    LL_OT_RefreshSelectedLights,
    LL_OT_RefreshSelectedMeshes,
    LL_OT_RefreshSelectedCollections,
    LL_OT_RefreshAllLights,
    LL_OT_ResetLights,
    LL_OT_RefreshAllMeshes,
    LL_OT_ResetMeshes,
    LL_OT_ResetCollections,
    LL_OT_Link,
    LL_OT_Unlink,
    LL_UL_LightList_UI,
    LL_UL_MeshList_UI,
    LL_UL_CollectionList_UI,
    LL_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.ll_light_items = bpy.props.CollectionProperty(type=LL_LightItem)
    bpy.types.Scene.ll_mesh_items = bpy.props.CollectionProperty(type=LL_MeshItem)
    bpy.types.Scene.ll_collection_items = bpy.props.CollectionProperty(type=LL_CollectionItem)
    
    bpy.types.Scene.ll_light_index = bpy.props.IntProperty(default=-1)
    bpy.types.Scene.ll_mesh_index = bpy.props.IntProperty(default=-1)
    bpy.types.Scene.ll_collection_index = bpy.props.IntProperty(default=-1)
    
    update_light_items(bpy.context.scene, bpy.context)
    update_mesh_items(bpy.context.scene, bpy.context)
    update_collection_items(bpy.context.scene, bpy.context)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.ll_light_items
    del bpy.types.Scene.ll_mesh_items
    del bpy.types.Scene.ll_collection_items
    del bpy.types.Scene.ll_light_index
    del bpy.types.Scene.ll_mesh_index
    del bpy.types.Scene.ll_collection_index

if __name__ == "__main__":
    register()
