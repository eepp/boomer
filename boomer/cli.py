# Copyright (c) 2021 Philippe Proulx <eepp.ca>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import fileinput
import boomer.api
import boomer
import sys
import re


def _parse_args():
    parser = argparse.ArgumentParser(description=boomer.__description__)
    parser.add_argument('--config', '-c', action='append',
                        help='Configure un algorithme sophistiqué')
    parser.add_argument('--non', '-n', action='append', nargs=1,
                        help='Désactive un algorithme sophistiqué')
    parser.add_argument('--graine', '-g', nargs=1, type=int,
                        help='Règle la graine du générateur de nombres aléatoires')
    parser.add_argument('--facteur', '-f', nargs=1, type=float,
                        help="Facteur à appliquer à chaque ratio d'algorithme sophistiqué")
    parser.add_argument('--version', '-V', action='version',
                        version=f'boomer {boomer.__version__}',
                        help='Affiche la version et quitte')
    parser.add_argument('input', metavar='INPUT', nargs='?', help='Entrée')
    return parser.parse_args()


def _run(args):
    # Convertir les arguments en configurations
    algo_cfgs = boomer.api._default_algo_cfgs()

    if args.config is not None:
        for arg in args.config:
            m = re.match(r'^([a-z]+)\s*=\s*(\d+)\s*:\s*(\d+)$', arg.strip())

            if not m:
                raise RuntimeError(f'Erreur: Format incompatible: {arg}')

            algo_cfgs[m.group(1)] = [int(m.group(2)), int(m.group(3))]

    if args.non is not None:
        for arg in args.non:
            algo_cfgs[arg[0]] = None

    if args.facteur is not None:
        for algo_cfg in algo_cfgs.values():
            if type(algo_cfg) is list:
                algo_cfg[0] *= args.facteur[0]

    seed = None

    if args.graine is not None:
        seed = args.graine[0]

    if args.input is None:
        # Entrée standard
        for line in fileinput.input():
            line = line.strip('\n')
            print(boomer.boomer(line, algo_cfgs, seed))
    else:
        print(boomer.boomer(args.input, algo_cfgs, seed))


def _main():
    try:
        _run(_parse_args())
    except Exception as exc:
        raise
        print(exc, file=sys.stderr)
        sys.exit(1)
