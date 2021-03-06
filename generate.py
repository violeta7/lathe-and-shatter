# coding: utf-8
# Copyright 2018 Artificial Intelligence Research Institute(AIRI), Korea
#
# This file is part of lathe-and-shatter.
# lathe-and-shatter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lathe-and-shatter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with lathe-and-shatter.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import print_function,division,absolute_import
import sys
from simple_svg import normalize_svg

import os
import subprocess
import json
import numpy as np
import matplotlib
from scipy.spatial import Voronoi

try: matplotlib.use('Agg')
except: pass

from parse_svg_path import parse_svg_path
from bezier_to_lineseg import bezier_to_lineseg
from lathe_path import lathe_path
from lathe_path import save_mesh
from tetgen_object import load_tetgen, find_vertex_group, find_element_group, rebuild_submesh, rebuild_submesh2

svg_path_A = '''
m 391.70976,851.54669 c 34.27007,-0.008 71.71313,-7.19875
101.93595,13.63887 22.69871,19.92007 58.04281,3.73196 49.27057,-27.83489
-7.42351,-33.89336 -17.8381,-75.4953 -20.76928,-110.26026
-8.10378,-67.27212 -11.74769,-115.35715 14.31191,-161.2026
26.0596,-45.84545 48.11138,-88.67184 59.80266,-124.06768
11.69128,-35.39584 20.08866,-65.99212 24.70468,-99.91615 0.34219,-36.23155
-34.34188,-58.10628 -59.77117,-77.93939 -22.23515,-12.80355
-25.84577,-39.51341 -36.09895,-59.87042 -34.55894,-10.05167
-21.60299,42.42532 -2.74272,53.66117 23.91321,25.40224 58.26754,45.0354
65.532,82.13536 10.3486,46.08391 -14.84571,89.48711 -32.21182,130.63696
-23.19916,50.76089 -54.16657,101.67171 -66.76628,153.50172
-12.59971,51.83001 7.05534,94.55435 12.2199,141.5473 2.08716,19.53932
12.55321,30.24752 10.81054,57.76824 -1.74267,27.52072 -35.49165,10.32954
-57.11444,7.47291 -21.62279,-2.85663 -42.9164,-1.12153 -64.02263,-1.03146
'''

svg_path_B = '''
m 32,872.3622 c 85.00366,0.46231 163.65989,-1.46892 217.51345,4.00054
53.85355,5.46946 72.88238,28.16978 74.36234,35.99567 15.6648,-1.77952
34.72603,-2.20097 56.73497,-0.16865 8.69378,-73.59952 3.53928,-153.31612
25.38924,-222.82756 21.84996,-69.51144 75.92261,-101.73139 98,-156
24.18459,-57.33333 24.27435,-115.93005 11,-172 -9.05665,-33.06504
-25.67515,-61.33816 -52,-84 -26.32485,-22.66184 -41.87658,-32.57509
-58,-40 -16.12342,-7.42491 -13.75092,-16.70175 0,-30 13.75092,-13.29825
49.60538,-32.45763 30,-46 -19.60538,-13.54237 -33.27204,-3.77275
-57,10 -23.72796,13.77275 -63.62532,33.33373 -58,50 8.47183,34.14528
58.37288,47.54028 82,71 23.62712,23.45972 33.49236,43.40268 47,78
12.70482,54.66667 8.19076,106.99679 -14,164 -22.15739,49.96502
-47.83344,101.58856 -75,148 -27.16656,46.41144 16.39025,159.58211
-35.37051,170.56587 -47.32823,5.02241 -93.26638,-6.12352
-138.62949,-5.56587 -45.36311,0.55765 -85.5124,-1.33296 -153.442715,7.2e-4
'''

svg_path_C = '''
m 72.9375,723.4247 c 34.16543,-0.28679 68.96657,-2.44188 102.5976,4.43271
13.76815,3.12321 14.41144,10.92511 16.30184,27.56522 7.24807,-0.24516
14.72789,-0.36454 21.83033,-0.27069 2.22108,-18.5269 6.77972,-23.2246
36.39811,-41.68574 31.99081,-19.3637 61.90677,-24.75747 92.32702,-38.87459
30.42025,-14.11712 47.28302,-20.99969 80.43205,-42.84689 33.14903,-21.8472
81.74098,-55.86091 105.73097,-79.43994 23.98999,-23.57903
23.41466,-47.65451 18.27888,-51.48078 -5.13578,-3.82627 -23.95785,11.30215
-49.21251,36.7587 -25.25466,25.45655 -35.06842,31.98461 -62.76063,54.57486
-27.69221,22.59025 -53.65612,38.66052 -101.85371,56.08804
-48.19759,17.42752 -123.73552,39.16954 -170.67772,40.91027
-46.9422,1.74073 -60.93221,2.68137 -90.32973,1.20633
'''

def main(args):

    num_fracs = args.num_fracs
    random_seed = args.random_seed
    output_prefix = args.output_prefix
    user_shape = args.user_shape
    base_shape = args.base_shape
    rand_perturbation = args.rand_perturbation
    tolerance = args.tolerance
    simplify_eps = args.simplify_eps
    num_divisions = args.num_divisions
    cap_start = args.cap_start
    cap_end = args.cap_end
    use_map_xz = args.map_coords == 'xz'

    if user_shape is None:
        if 0 == base_shape:
            base_shape = np.random.randint(1,4)
        if base_shape == 2:
            user_shape = svg_path_B
        elif base_shape == 3:
            user_shape = svg_path_C
        elif base_shape == 1:
            user_shape = svg_path_A
        else: # random choice
            assert False
    else:
        base_shape = 0

    if 0 == random_seed:
        random_seed = np.random.randint(0,1000000)
        print('random_seed auto generated',random_seed,file=sys.stderr)

    if rand_perturbation:
        rand_perturbation = np.random.randint(0, rand_perturbation*10000)/10000
        print('rand_perturbation will be used',rand_perturbation,file=sys.stderr)

    prefix = '{:s}_{:d}_{:d}_{:d}'.format(output_prefix,num_fracs,base_shape,random_seed)

    # create output directory if not exists
    output_dir = os.path.dirname(output_prefix)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)


    # load svg path, extract curve points
    svg_path = normalize_svg(user_shape)

    with open(prefix + '_path.svg','w') as f:
        f.write(svg_path)

    # extract curve points from svg path
    curve_points = parse_svg_path(svg_path, rand_perturbation=rand_perturbation, rand_seed=random_seed)

    # convert curves to line segments
    points = bezier_to_lineseg(curve_points, tolerance=tolerance, simplify_eps=simplify_eps)
    # lathe line segments to build 3-d surface mesh
    nodes, texcoords, triangles = lathe_path(points, num_divisions=num_divisions, cap_start=cap_start, cap_end=cap_end, use_map_xz=use_map_xz)

    # make voronoi shatter pattern


    num_groups = num_fracs

    np.random.seed(random_seed)
    cells = np.random.uniform([0.0,0.0],[1.0,1.0],size=[num_groups,2])

    if use_map_xz:
        voronoi = Voronoi(cells)
        voronoi_points = voronoi.points[:]
        voronoi_group = np.arange(len(voronoi_points))
    else:
        cells_mirrored = np.concatenate([cells,cells + [-1.0, 0.0],cells + [1.0, 0.0],],axis=0)
        voronoi = Voronoi(cells_mirrored)
        voronoi_points = voronoi.points[:]
        voronoi_group = np.arange(len(voronoi_points))
        voronoi_group[num_groups:num_groups*2] -= num_groups
        voronoi_group[num_groups*2:] -= num_groups * 2

    shatter_filename = prefix + '.voronoi.json'
    voronoi_shatter = {
        'num_groups': num_groups,
        'point_group': voronoi_group.tolist(),
        'point': voronoi.points.tolist(),
    }
    with open(shatter_filename,'w') as f:
        json.dump(voronoi_shatter,f)

    # create boundary markers for tetgen
    # markers are negative numbers <= -2
    vert_group = find_vertex_group(texcoords,voronoi_points,voronoi_group)
    face_group = find_element_group(triangles,texcoords,voronoi_points,voronoi_group)

    # create .smesh file to input to tetgen
    # put u, v coords into node attributes (#=2)
    # put group codes into vertice boundary markers, and into face boundary markers
    smesh_filename = prefix + '.smesh'
    with open(smesh_filename,'w') as f:
        save_mesh(f,nodes,triangles,node_attrs=texcoords,node_boundary_markers=vert_group,face_boundary_markers=face_group)

    # call `tetgen` executable to make 3-d mesh (delaunay tetrahedralization)
    tetgen_args = [
        "tetgen",
        "-p",
        smesh_filename,
    ]
    proc = subprocess.Popen(tetgen_args,bufsize=0,universal_newlines=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print(line.strip(),file=sys.stderr)

    tetgen_out_filebase = prefix + '.1'
    assert os.path.exists(tetgen_out_filebase + '.ele')

    # read generated object files (.ele, .face, .node)
    obj1 = load_tetgen(tetgen_out_filebase)

    # group 별로 파편 생성, 출력

    for i in range(num_fracs):
        part_name = prefix + '_part_{:d}'.format(i+1)
        ptcloud_name = prefix + '_part_{:d}.npy'.format(i+1)

        print('writing part',part_name,file=sys.stderr)

        sel = -(i+2)

        new_obj, new_ptcloud = rebuild_submesh2(obj1,sel,voronoi_points,voronoi_group)
        new_obj.save(part_name)

        print('writing point-cloud',ptcloud_name,file=sys.stderr)

        with open(ptcloud_name,'wb') as f:
            np.save(f, new_ptcloud)
        del new_obj


from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--base_shape',type=int,default=0) # 0 == random choice([1,2,3])
    parser.add_argument('--num_fracs',type=int,default=11)
    parser.add_argument('--output_prefix',type=str,default='outputs/generated')
    parser.add_argument('--user_shape',type=str,default=None)
    parser.add_argument('--rand_perturbation',type=float,default=0.08)
    parser.add_argument('--random_seed',type=int,default=0) # 802087) # 0 == random seed
    parser.add_argument('--tolerance',type=float,default=0.02)
    parser.add_argument('--simplify_eps',type=float,default=0.001)
    parser.add_argument('--num_divisions',type=int,default=360)
    parser.add_argument('--cap_start',type=int,default=0)
    parser.add_argument('--cap_end',type=int,default=0)
    parser.add_argument('--map_coords',type=str,default='uv') # or you can choose 'xz'

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    main(args)
