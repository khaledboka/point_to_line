from osgeo import ogr, osr
import re


class PointsToMultiPath(object):
    def __init__(self,
                 connection_string,
                 in_layer_name,
                 out_layer_name,
                 sort_by_attr,
                 group_by_attr,
                 line_features=None
                 ):
        self.in_layer_name = str(in_layer_name)
        self.out_layer_name = str(out_layer_name)
        self.sort_by_attr = str(
            sort_by_attr) if sort_by_attr is not None else None
        self.group_by_attr = str(
            group_by_attr) if group_by_attr is not None else None
        self.line_features = line_features if line_features is not None else None
        self.new_out_field_name = 'ogc_line_name'
        self.connection_string = connection_string

    def start_connection(self):
        self.conn = ogr.Open(self.connection_string)

    def execute(self):
        self.get_in_layer()

        self.create_out_layer()
        self.create_out_features_field()
        self.create_features_dict()
        self.out_features = self.create_out_features()

        self.commit_transactions()

    def get_in_layer(self):
        self.in_layer = self.conn.GetLayer(self.in_layer_name)
        self.in_layerDefn = self.in_layer.GetLayerDefn()
        self.srs = self.in_layer.GetSpatialRef()
        self.group_by_index = self.get_field_index(
            self.group_by_attr) if self.group_by_attr is not None else None
        self.sort_by_index = self.get_field_index(
            self.sort_by_attr) if self.sort_by_attr is not None else None

    def create_out_layer(self):
        # create an out layer in postgres
        self.conn.CreateLayer(
            self.out_layer_name,
            geom_type=ogr.wkbLineString,
            srs=self.srs,
            options=['OVERWRITE=YES']
        )
        self.out_layer = self.conn.GetLayer(self.out_layer_name)
        self.out_featureDefn = self.out_layer.GetLayerDefn()

    def create_out_features_field(self):
        field_defn = ogr.FieldDefn(self.new_out_field_name, ogr.OFTString)
        self.out_layer.StartTransaction()
        self.out_layer.CreateField(field_defn)
        self.out_layer.CommitTransaction()

    def get_field_index(self, attr):
        for i in range(self.in_layerDefn.GetFieldCount()):
            if (self.in_layerDefn.GetFieldDefn(i).GetName() == attr):
                return i

    def create_features_dict(self):
        features_dict = {}
        # consider all point features in one line feature if not (group by)
        if self.group_by_index is None:
            features_dict['single_feature'] = [f for f in self.in_layer]
            self.features_dict = features_dict
            return features_dict
        for f in self.in_layer:
            line_name = str(f[self.group_by_index])
            # If user selected some line features
            if self.line_features:
                # if line feature in the selected line features
                if line_name in self.line_features:
                    try:
                        # if the list of features
                        features_dict[line_name].append(f)
                    except:
                        # create list of features if not existing
                        features_dict[line_name] = []
                        features_dict[line_name].append(f)
                else:
                    # TODO: raise error or handle skipping
                    pass
            # Consider all line features are selected
            else:
                try:
                    # if the list of features
                    features_dict[line_name].append(f)
                except:
                    # create list of features if not existing
                    features_dict[line_name] = []
                    features_dict[line_name].append(f)
        self.features_dict = features_dict
        return features_dict

    def get_duplicated_features(self):
        ''' returns dictionary with duplicated and unique features based on sort by attribute 
            result = {
                key:{
                    unique:[],
                    duplicate:[],
                }
            }
        '''
        result = {}
        for i, key in enumerate(self.features_dict, start=1):
            features = self.features_dict[key]
            
            # remove all duplicate features in case of sort by, Please look at Ex:
            # Ex: [a, a, b, c, d] => unique = [b, c, d], duplicates = [a, a]
            if self.sort_by_index is not None:
                unique_features = {}
                duplicate_features = []
                for f in features:
                    # Check if f exist u
                    try:
                        u = unique_features[f[self.sort_by_index]]
                        # 1. Add current featute to duplicates
                        duplicate_features.append(f)
                        # 2. move feature from unique to duplicates
                        duplicate_features.append(u)
                        # 3. remove it from unique
                        del unique_features[f[self.sort_by_index]]
                    except:
                        # feature is not duplicated
                        # Append it to unique
                        unique_features[f[self.sort_by_index]] = f

                result[key] = {}
                # result[key]['unique'] = [f[self.sort_by_index] for f in unique_features]
                result[key]['duplicate'] = [f[self.sort_by_index] for f in duplicate_features]
        return result

    def create_out_features(self):
        # Lines Creation Process:
        out_features = []
        for i, key in enumerate(self.features_dict, start=1):
            features = self.features_dict[key]
            sorted_features = features
            
            # remove all duplicate features in case of sort by, Please look at Ex:
            # Ex: [a, a, b, c, d] => unique = [b, c, d], duplicates = [a, a]
            if self.sort_by_index is not None:
                unique_features = {}
                duplicate_features = []
                for f in features:
                    # Check if f exist u
                    try:
                        u = unique_features[f[self.sort_by_index]]
                        # 1. Add current featute to duplicates
                        duplicate_features.append(f)
                        # 2. move feature from unique to duplicates
                        duplicate_features.append(u)
                        # 3. remove it from unique
                        del unique_features[f[self.sort_by_index]]
                    except:
                        # feature is not duplicated
                        # Append it to unique
                        unique_features[f[self.sort_by_index]] = f
                features = [unique_features[key] for key in unique_features.keys()]
                
            # human / natural sorting features by sort attr inside the dict:
            if self.sort_by_index is not None:
                def convert(text): return int(
                    text) if text.isdigit() else text.lower()

                def alphanum_key(key): return [
                    convert(s) for s in re.split('([0-9]+)', str(key[self.sort_by_index]))
                ]
                sorted_features = sorted(features, key=alphanum_key)

            # create a new line geometry
            line = ogr.Geometry(ogr.wkbLineString)
            for feat in sorted_features:
                geom = feat.GetGeometryRef()
                line.AddPoint(geom.GetX(), geom.GetY())

            # Create a new feature
            out_feature = ogr.Feature(self.out_featureDefn)

            # Set Feature Geometry
            out_feature.SetGeometry(line)

            # Set field [line_name] with value key of the features dict
            out_feature.SetField(self.new_out_field_name, key)

            out_features.append(out_feature)
        return out_features

    def commit_transactions(self):
        # Start transaction with postgres and create feature(table row)
        for feature in self.out_features:
            self.out_layer.StartTransaction()
            self.out_layer.CreateFeature(feature)
            self.out_layer.CommitTransaction()

    def delete_layer(self, layer_name):
        print('Deleting layer \'{}\' from database'.format(layer_name))
        self.conn.DeleteLayer(layer_name)

    def close_connection(self):
        self.conn = None
