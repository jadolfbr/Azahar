import pymol
from pymol import cmd
import os, sys
path = os.path.dirname(__file__)
sys.path.append(path)
from torsionals import set_phi, set_psi, get_phi, get_psi
try:
    from energy import minimize
    babel = True
except ImportError:
    babel = False

def read_input(matrix):
    """ Reads a the file that specifies the connectivity of an specific glycan. 
    Returns two lists, one containing the identity of the monosacharides and 
    another indicating the connectivity.
    """    
    fd = open(matrix).readlines()
    bonds = []
    for line in fd:
        row = line.split()
        bonds.append((int(row[0]), row[1], int(row[2]),
        row[3], int(row[4]), int(row[5])))

    residues = [''] * (len(bonds) + 1)
    for line in fd:
        row = line.split()
        residues[int(row[0])] = row[1]
        residues[int(row[2])] = row[3]
    return residues, bonds


def fast_min(pose, cycles):
    """Perform a "Molecular Scuplting" of a molecule (pose).
    Molecular sculpting works like a real-time energy minimizer, except that 
    it isn't minimizing the energy. Instead, its just trying to return local 
    atomic geometries (bonds, angles, chirality, planarity) to the configuration
    the molecules possess when they were first loaded into PyMOL."""
    
    cmd.sculpt_activate(pose)
    cmd.sculpt_iterate(pose, cycles=cycles)


def builder(residues, bonds, mol_name):
    """Using the list generated by read_input connects monosacharides in 
    a single oligosaccharide"""
    cmd.set('defer_updates', 'on')
    cmd.feedback('disable', 'executive', 'actions')
    every_object = cmd.get_object_list('all')
    if mol_name in every_object:
        cmd.delete(mol_name)
        every_object.remove(mol_name)
    if every_object:
        sel = 'not (' + ' or '.join(every_object) + ') and'
    else:
        sel = ''
    for i in range(0, len(residues)):
        res_name = residues[i]
        cmd.load(os.path.join(path, 'db_glycans', '%s.pdb' % res_name))
        cmd.set_name('%s' % res_name, '%s' % i)  #rename object (necessary to avoid repeating names)
        cmd.alter('%s' % i, 'resi = %s' % i)  #name residues for further referencing
        cmd.sort()
    for i in range(0, len(bonds)):
        resi_i, resi_j, atom_i, atom_j = bonds[i][0], bonds[i][2], bonds[i][4], bonds[i][5]
        if atom_i > atom_j:
            cmd.remove('%s (resi %s and name O%s+H%so)' % (sel, resi_j, atom_j, atom_j))
            cmd.remove('%s (resi %s and name H%so)' % (sel, resi_i, atom_i))
            cmd.fuse('%s (resi %s and name O%s)' % (sel, resi_i, atom_i), '%s (resi %s and name C%s)' % (sel, resi_j, atom_j))
        else:
            cmd.remove('%s (resi %s and name O%s+H%so)' % (sel, resi_i, atom_i, atom_i))
            cmd.remove('%s (resi %s and name H%so)' % (sel, resi_j, atom_j))
            cmd.fuse('%s (resi %s and name C%s)' % (sel, resi_i, atom_i), '%s (resi %s and name O%s)' % (sel, resi_j, atom_j))
    cmd.copy(mol_name, '%s' % len(bonds))
    for i in range(0, len(residues)):
        cmd.delete('%s' % i)
    for i in range(0, len(bonds)):
        set_phi(mol_name, bonds[i], -60)
        set_psi(mol_name, bonds[i], 120) 
    cmd.delete('pk1')
    cmd.delete('pk2')
    cmd.delete('pkbond')
    cmd.delete('pkmol')
    if babel:
        fast_min(mol_name, 5000)
        minimize(mol_name)
    else:
        fast_min(mol_name, 5000)
    cmd.feedback('enable', 'executive', 'actions')
    cmd.set('defer_updates', 'off')


