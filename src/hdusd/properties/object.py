#**********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#********************************************************************
import bpy

from pxr import UsdGeom, Gf

from . import HdUSDProperties, CachedStageProp
from ..export.object import get_transform_local
from ..utils import usd as usd_utils


GEOM_TYPES = ('Xform', 'SkelRoot')


class ObjectProperties(HdUSDProperties):
    bl_type = bpy.types.Object

    sdf_path: bpy.props.StringProperty(default="")
    cached_stage: bpy.props.PointerProperty(type=CachedStageProp)

    @property
    def is_usd(self):
        return bool(self.sdf_path)

    def get_prim(self):
        stage = self.cached_stage()
        if not stage:
            return None

        return stage.GetPrimAtPath(self.sdf_path)

    def sync_from_prim(self, root_obj, prim):
        prim_obj = self.id_data

        self.sdf_path = str(prim.GetPath())
        self.cached_stage.assign(prim.GetStage())

        prim_obj.name = prim.GetName()
        prim_obj.parent = root_obj
        prim_obj.matrix_local = usd_utils.get_xform_transform(UsdGeom.Xform(prim))
        prim_obj.hide_viewport = prim.GetTypeName() not in GEOM_TYPES

    def sync_to_prim(self):
        prim = self.get_prim()
        if not prim:
            return

        obj = self.id_data
        xform = UsdGeom.Xform(prim)
        xform.MakeMatrixXform().Set(Gf.Matrix4d(get_transform_local(obj)))


def depsgraph_update(depsgraph):
    if not depsgraph.updates:
        return

    upd = depsgraph.updates[0]
    obj = upd.id
    if not isinstance(obj, bpy.types.Object) or not obj.hdusd.is_usd:
        return

    obj.hdusd.sync_to_prim()
