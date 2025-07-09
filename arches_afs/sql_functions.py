import os
import uuid as GenUUID

from arches_afs import general_configs


ARCHES_V8_RESOURCE_INSTANCE_FUNCTION_FIX = """
-- FUNCTION: public.__arches_instance_view_update()

-- DROP FUNCTION IF EXISTS public.__arches_instance_view_update();

CREATE OR REPLACE FUNCTION public.__arches_instance_view_update()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
                declare
                    view_namespace text;
                    model_id uuid;
                    instance_id uuid;
                    transaction_id uuid;
                    edit_type text;
                begin
                    view_namespace = format('%s.%s', tg_table_schema, tg_table_name);
                    select obj_description(view_namespace::regclass, 'pg_class') into model_id;
                    if (TG_OP = 'DELETE') then
                        delete from public.resource_instances where resourceinstanceid = old.resourceinstanceid;
                        insert into bulk_index_queue (resourceinstanceid, createddate)
                            values (old.resourceinstanceid, current_timestamp) on conflict do nothing;
                        insert into edit_log (
                            resourceclassid,
                            resourceinstanceid,
                            edittype,
                            timestamp,
                            note,
                            transactionid
                        ) values (
                            model_id,
                            old.resourceinstanceid,
                            'delete',
                            now(),
                            'loaded via SQL backend',
                            public.uuid_generate_v1mc()
                        );
                        return old;
                    else
                        instance_id = new.resourceinstanceid;
                        if instance_id is null then
                            instance_id = public.uuid_generate_v1mc();
                        end if;

                        if (new.transactionid is null) then
                            transaction_id = public.uuid_generate_v1mc();
                        else
                            transaction_id = new.transactionid;
                        end if;

                        if (TG_OP = 'UPDATE') then
                            edit_type = 'edit';
                            if (transaction_id = old.transactionid) then
                                transaction_id = public.uuid_generate_v1mc();
                            end if;
                            update public.resource_instances
                            set createdtime = new.createdtime,
                                legacyid = new.legacyid
                            where resourceinstanceid = instance_id;
                        elsif (TG_OP = 'INSERT') then
                            edit_type = 'create';
                            insert into public.resource_instances(
                                resourceinstanceid,
                                graphid,
                                legacyid,
                                createdtime,
								 resource_instance_lifecycle_state_id
                            ) values (
                                instance_id,
                                model_id,
                                new.legacyid,
                                now(),
								'f75bb034-36e3-4ab4-8167-f520cf0b4c58'::uuid
                            );
                        end if;
                        insert into bulk_index_queue (resourceinstanceid, createddate)
                            values (instance_id, current_timestamp) on conflict do nothing;
                        insert into edit_log (
                            resourceclassid,
                            resourceinstanceid,
                            edittype,
                            timestamp,
                            note,
                            transactionid
                        ) values (
                            model_id,
                            instance_id,
                            edit_type,
                            now(),
                            'loaded via SQL backend',
                            transaction_id
                        );
                        return new;
                    end if;
                end;
            
$BODY$;

ALTER FUNCTION public.__arches_instance_view_update()
    OWNER TO postgres;
"""




POSTGRESQL_PERFORMANCE_FIX = """
create or replace function __arches_tile_view_update() returns trigger as $$
declare
    view_namespace text;
    group_id uuid;
    graph_id uuid;
    parent_id uuid;
    tile_id uuid;
    transaction_id uuid;
    json_data json;
    old_json_data jsonb;
    edit_type text;
begin
    select graphid into graph_id from nodes where nodeid = group_id;
    view_namespace = format('%s.%s', tg_table_schema, tg_table_name);
    select obj_description(view_namespace::regclass, 'pg_class') into group_id;
    if (TG_OP = 'DELETE') then
        select tiledata into old_json_data from tiles where tileid = old.tileid;
        delete from resource_x_resource where tileid = old.tileid;
        delete from public.tiles where tileid = old.tileid;
        insert into bulk_index_queue (resourceinstanceid, createddate)
            values (old.resourceinstanceid, current_timestamp) on conflict do nothing;
        insert into edit_log (
            resourceclassid,
            resourceinstanceid,
            nodegroupid,
            tileinstanceid,
            edittype,
            oldvalue,
            timestamp,
            note,
            transactionid
        ) values (
            graph_id,
            old.resourceinstanceid,
            group_id,
            old.tileid,
            'tile delete',
            old_json_data,
            now(),
            'loaded via SQL backend',
            public.uuid_generate_v1mc()
        );
        return old;
    else
        select __arches_get_json_data_for_view(new, tg_table_schema, tg_table_name) into json_data;
        select __arches_get_parent_id_for_view(new, tg_table_schema, tg_table_name) into parent_id;
        tile_id = new.tileid;
        if (new.transactionid is null) then
            transaction_id = public.uuid_generate_v1mc();
        else
            transaction_id = new.transactionid;
        end if;

        if (TG_OP = 'UPDATE') then
            select tiledata into old_json_data from tiles where tileid = tile_id;
            edit_type = 'tile edit';
            if (transaction_id = old.transactionid) then
                transaction_id = public.uuid_generate_v1mc();
            end if;
            update public.tiles
            set tiledata = json_data,
                nodegroupid = group_id,
                parenttileid = parent_id,
                resourceinstanceid = new.resourceinstanceid
            where tileid = new.tileid;
        elsif (TG_OP = 'INSERT') then
            old_json_data = null;
            edit_type = 'tile create';
            if tile_id is null then
                tile_id = public.uuid_generate_v1mc();
            end if;
            insert into public.tiles(
                tileid,
                tiledata,
                nodegroupid,
                parenttileid,
                resourceinstanceid
            ) values (
                tile_id,
                json_data,
                group_id,
                parent_id,
                new.resourceinstanceid
            );
        end if;
        perform __arches_refresh_tile_resource_relationships(tile_id);
        insert into bulk_index_queue (resourceinstanceid, createddate)
            values (new.resourceinstanceid, current_timestamp) on conflict do nothing;
        insert into edit_log (
            resourceclassid,
            resourceinstanceid,
            nodegroupid,
            tileinstanceid,
            edittype,
            newvalue,
            oldvalue,
            timestamp,
            note,
            transactionid
        ) values (
            graph_id,
            new.resourceinstanceid,
            group_id,
            tile_id,
            edit_type,
            json_data::jsonb,
            old_json_data,
            now(),
            'loaded via SQL backend',
            transaction_id
        );
        return new;
    end if;
    end;
$$ language plpgsql;
"""



DIASABLE_TRIGGERS_BEFORE_INSERTS = """
/*
ALTER TABLE TILES DISABLE TRIGGER __arches_check_excess_tiles_trigger;
ALTER TABLE TILES DISABLE TRIGGER __arches_trg_update_spatial_attributes;
*/
"""

REACTIVATE_TRIGGERS_AFTER_INSERTS = """
/*
ALTER TABLE TILES ENABLE TRIGGER __arches_check_excess_tiles_trigger;
ALTER TABLE TILES ENABLE TRIGGER __arches_trg_update_spatial_attributes;
*/
"""

POSTGRESQL_AFTER_ETL_FUNCTION = """
select * from refresh_geojson_geometries();
"""


FIX_PHYS_PLACE_RESOURCE_LINK = """
/*
graphid = 'cc8ed633-b25b-11e9-a13a-a4d18cec433a' (place model)
graphid = '9519cb4f-b25b-11e9-8c7b-a4d18cec433a' (physical thing model)

nodeid = '7f13dbde-d2bd-11e9-9adc-a4d18cec433a' ('addition_to_collection_added_to')
nodeid = '57f2d840-d2bd-11e9-a411-a4d18cec433a' ('addition_to_collection_location')
*/



SELECT * 
FROM public.resource_x_resource AS r_x_r
JOIN public.resource_instances AS r_to ON r_x_r.resourceinstanceidto = r_to.resourceinstanceid
JOIN public.resource_instances AS r_from ON r_x_r.resourceinstanceidfrom = r_from.resourceinstanceid
WHERE r_to.graphid = 'cc8ed633-b25b-11e9-a13a-a4d18cec433a'
AND r_from.graphid = '9519cb4f-b25b-11e9-8c7b-a4d18cec433a'
AND r_x_r.nodeid = '7f13dbde-d2bd-11e9-9adc-a4d18cec433a'



/* UPDATE the resource_x_resource nodeid to be correct */

UPDATE public.resource_x_resource AS r_x_r_up
SET nodeid = '57f2d840-d2bd-11e9-a411-a4d18cec433a'
FROM public.resource_x_resource AS r_x_r
JOIN public.resource_instances AS r_to ON r_x_r.resourceinstanceidto = r_to.resourceinstanceid
JOIN public.resource_instances AS r_from ON r_x_r.resourceinstanceidfrom = r_from.resourceinstanceid
WHERE r_to.graphid = 'cc8ed633-b25b-11e9-a13a-a4d18cec433a'
AND r_from.graphid = '9519cb4f-b25b-11e9-8c7b-a4d18cec433a'
AND r_x_r.nodeid = '7f13dbde-d2bd-11e9-9adc-a4d18cec433a'
AND r_x_r_up.resourcexid = r_x_r.resourcexid







SELECT t_r.tileid, r_x_r.resourcexid , t_r.tiledata, r_from.name AS from_name, r_to.name AS to_name 
FROM public.tiles AS t_r
JOIN public.resource_x_resource AS r_x_r ON r_x_r.tileid = t_r.tileid
JOIN public.resource_instances AS r_to ON r_x_r.resourceinstanceidto = r_to.resourceinstanceid
JOIN public.resource_instances AS r_from ON r_x_r.resourceinstanceidfrom = r_from.resourceinstanceid
WHERE r_to.graphid = 'cc8ed633-b25b-11e9-a13a-a4d18cec433a'
AND r_from.graphid = '9519cb4f-b25b-11e9-8c7b-a4d18cec433a'
AND  t_r.nodegroupid = '57f25133-d2bd-11e9-9131-a4d18cec433a'
AND t_r.tiledata::jsonb ? '7f13dbde-d2bd-11e9-9adc-a4d18cec433a'
AND jsonb_array_length(t_r.tiledata->'7f13dbde-d2bd-11e9-9adc-a4d18cec433a') >= 2
;








UPDATE public.tiles AS t_up
SET tiledata = jsonb_set(
    jsonb_set(
        t_up.tiledata,
        '{7f13dbde-d2bd-11e9-9adc-a4d18cec433a}',
        (t_up.tiledata->'7f13dbde-d2bd-11e9-9adc-a4d18cec433a') - 1 -- Remove the second element from 'a_key'
    ),
    '{57f2d840-d2bd-11e9-a411-a4d18cec433a}',
    jsonb_build_array(((t_up.tiledata->'7f13dbde-d2bd-11e9-9adc-a4d18cec433a')->>1)::jsonb)::jsonb -- Create a new array with the second element of 'a_key'
)
FROM public.tiles AS t_r
JOIN public.resource_x_resource AS r_x_r ON r_x_r.tileid = t_r.tileid
JOIN public.resource_instances AS r_to ON r_x_r.resourceinstanceidto = r_to.resourceinstanceid
JOIN public.resource_instances AS r_from ON r_x_r.resourceinstanceidfrom = r_from.resourceinstanceid
WHERE r_to.graphid = 'cc8ed633-b25b-11e9-a13a-a4d18cec433a'
AND r_from.graphid = '9519cb4f-b25b-11e9-8c7b-a4d18cec433a'
AND  t_r.nodegroupid = '57f25133-d2bd-11e9-9131-a4d18cec433a'
AND t_r.tiledata::jsonb ? '7f13dbde-d2bd-11e9-9adc-a4d18cec433a'
AND t_r.tileid = t_up.tileid
AND jsonb_array_length(t_up.tiledata->'7f13dbde-d2bd-11e9-9adc-a4d18cec433a') >= 2

;


"""