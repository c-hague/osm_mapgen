import json
import os.path
import warnings
import logging
import sys
logging.basicConfig(filename='std.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

class ModelGenerator(object):
    """Provides the Modeler 3D interface.
    """

    def __init__(self, application):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        return

    def __get__(self, instance, owner):
        self._app = instance
        return self

    def import_from_openstreet_map(
            self,
            latitude_longitude,
            env_name="default",
            terrain_radius=500,
            include_osm_buildings=True,
            including_osm_roads=True,
            include_osm_trees=True,
            import_in_aedt=False,
            plot_before_importing=False,
            z_offset=2,
            road_step=3,
            road_width=8,
            create_lightweigth_part=True,
            save_nodes=False,
    ):
        """Import OpenStreet Maps into AEDT.

        Parameters
        ----------
        latitude_longitude : list
            Latitude and longitude.
        env_name : str, optional
            Name of the environment used to create the scene. The default value is ``"default"``.
        terrain_radius : float, int
            Radius to take around center. The default value is ``500``.
        include_osm_buildings : bool
            Either if include or not 3D Buildings. Default is ``True``.
        including_osm_roads : bool
            Either if include or not road. Default is ``True``.
        import_in_aedt : bool
            Either if import stl after generation or not. Default is ``True``.
        plot_before_importing : bool
            Either if plot before importing or not. Default is ``True``.
        z_offset : float
            Road elevation offset. Default is ``0``.
        road_step : float
            Road simplification steps in meter. Default is ``3``.
        road_width : float
            Road width  in meter. Default is ``8``.
        create_lightweigth_part : bool
            Either if import as lightweight object or not. Default is ``True``.

        Returns
        -------
        dict
            Dictionary of generated infos.

        """
        from osm import BuildingsPrep
        from osm import RoadPrep
        from osm import TerrainPrep
        from osm import TreesPrep

        # output_path = self._app.working_directory
        output_path = "."

        parts_dict = {}
        # instantiate terrain module
        terrain_prep = TerrainPrep(cad_path=output_path)
        terrain_geo = terrain_prep.get_terrain(latitude_longitude, max_radius=terrain_radius, grid_size=30)
        terrain_stl = terrain_geo["file_name"]
        terrain_mesh = terrain_geo["mesh"]
        terrain_dict = {"file_name": terrain_stl, "color": "brown", "material": "earth"}
        parts_dict["terrain"] = terrain_dict
        building_mesh = None
        road_mesh = None
        if include_osm_buildings:
            self.logger.info("Generating Building Geometry")
            building_prep = BuildingsPrep(cad_path=output_path)
            building_geo = building_prep.generate_buildings(
                latitude_longitude, terrain_mesh, max_radius=terrain_radius * 0.8
            )
            building_stl = building_geo["file_name"]
            building_mesh = building_geo["mesh"]
            building_dict = {"file_name": building_stl, "color": "grey", "material": "concrete"}
            parts_dict["buildings"] = building_dict

        if include_osm_trees:
            self.logger.info("Generating Tree Geometry")
            tree_prep = TreesPrep(cad_path=output_path)
            tree_geo = tree_prep.generate_trees(
                latitude_longitude, terrain_mesh, max_radius=terrain_radius * 0.8
            )
            tree_stl = tree_geo["file_name"]
            tree_mesh = tree_geo["mesh"]
            tree_dict = {"file_name": tree_stl, "color": "green", "material": "wood"}
            parts_dict["trees"] = tree_dict

        if including_osm_roads:
            self.logger.info("Generating Road Geometry")
            road_prep = RoadPrep(cad_path=output_path)
            road_geo = road_prep.create_roads(
                latitude_longitude,
                terrain_mesh,
                max_radius=terrain_radius,
                z_offset=z_offset,
                road_step=road_step,
                road_width=road_width,
                save_nodes=save_nodes,
            )

            road_stl = road_geo["file_name"]
            road_mesh = road_geo["mesh"]
            road_dict = {"file_name": road_stl, "color": "black", "material": "asphalt"}
            parts_dict["roads"] = road_dict

        json_path = os.path.join(output_path, env_name + ".json")

        scene = {
            "name": env_name,
            "version": 1,
            "type": "environment",
            "center_lat_lon": latitude_longitude,
            "radius": terrain_radius,
            "include_buildings": include_osm_buildings,
            "include_roads": including_osm_roads,
            "include_trees": include_osm_trees,
            "parts": parts_dict,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scene, f, indent=4)

        self.logger.info("Done...")
        return scene
