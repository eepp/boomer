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

import re
import random
import collections
import boomer.verbs as boomer_verbs


class _Token:
    def __init__(self, text, has_trailing_space):
        self._text = text
        self._has_trailing_space = has_trailing_space

    @property
    def lower(self):
        return self._text.lower()

    @property
    def upper(self):
        return self._text.upper()

    @property
    def starts_with_lower(self):
        return len(self._text) > 0 and self._text[0].islower()

    @property
    def starts_with_upper(self):
        return len(self._text) > 0 and self._text[0].isupper()

    @property
    def ends_with_lower(self):
        return len(self._text) > 0 and self._text[-1].islower()

    @property
    def ends_with_upper(self):
        return len(self._text) > 0 and self._text[-1].isupper()

    def __len__(self):
        return len(self._text)

    def __getitem__(self, index):
        return self._text[index]

    def __contains__(self, text):
        return text in self._text

    def __iter__(self):
        return iter(self._text)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

    def replace_suffix(self, suffix, rem_len=None, keep_form=True):
        if rem_len is None:
            rem_len = len(suffix)

        text = f'{self._text[:-rem_len]}{suffix}'

        if keep_form:
            self.replace_keep_form(text)
        else:
            self._text = text

    def replace_prefix(self, prefix, rem_len=None, keep_form=True):
        if rem_len is None:
            rem_len = len(prefix)

        text = f'{prefix}{self._text[rem_len:]}'

        if keep_form:
            self.replace_keep_form(text)
        else:
            self._text = text

    def replace_keep_form(self, text):
        if self._text.islower():
            self._text = text.lower()
        elif self._text.isupper():
            self._text = text.upper()
        elif self._text.istitle():
            self._text = text.capitalize()
        else:
            self._text = text

    @property
    def has_trailing_space(self):
        return self._has_trailing_space

    @has_trailing_space.setter
    def has_trailing_space(self, has_trailing_space):
        self._has_trailing_space = has_trailing_space

    def __repr__(self):
        return f'_Token({repr(self._text)}, {repr(self._has_trailing_space)})'


class _Algo:
    def __init__(self, true_false_weights):
        self._the_true_false_weights = true_false_weights

    @property
    def _true_false_weights(self):
        return self._the_true_false_weights

    @staticmethod
    def _random_bool(true_false_weights):
        return random.choices([True, False], true_false_weights)[0]

    @staticmethod
    def _choose_other_in_set(item, set):
        return random.choice(list(set - {item}))


class _TokenAlgo(_Algo):
    def filter(self, t):
        return True

    def trans(self, t):
        pass

    def process_tokens(self, tokens):
        self._apply_with_prob(tokens)

    def _apply_with_prob(self, tokens, true_false_weights=None):
        if true_false_weights is None:
            true_false_weights = self._true_false_weights

        tokens = [t for t in tokens if self.filter(t)]

        for t in tokens:
            if self._random_bool(true_false_weights):
                self.trans(t)


class _TextAlgo(_Algo):
    def process_text(self, text):
        raise NotImplementedError


# Monique s'occupe de quelques remplacements populaires simples, dont
# plusieurs homophones.
class _MoniqueAlgo(_TokenAlgo):
    _rep_sets = [
        {"c'est", 'ces', 'ses', 'sais', 'sait'},
        {'à', 'a'},
        {'ça', 'sa'},
        {'ce', 'se'},
        {'dans', "d'en"},
        {'la', 'là', "l'as"},
        {'ma', "m'a", "m'as"},
        {'ta', "t'a", "t'as"},
        {'mon', "m'ont", 'mont'},
        {'ton', "t'ont", 'thon'},
        {'leur', 'leurs', "l'heure"},
        {'mes', "m'es", "m'est", 'mets', 'met', 'mais', 'met'},
        {'ni', "n'y"},
        {'où', "ou"},
        {'on', 'ont'},
        {'parce', 'par ce', 'par se'},
        {'peu', 'peux', 'peut', 'peus'},
        {'peut-être', 'peut être', 'peu être'},
        {'près', 'prêt'},
        {"qu'en", 'quand', 'quant'},
        {'quelque', 'quelques', 'quel que', 'quels que', 'quelles que'},
        {"qu'elle", "qu'elles", 'quel', 'quels', 'quelle', 'quelles'},
        {"qu'il", "qu'ils"},
        {"s'en", 'sens', 'sent', 'sans', 'sang'},
        {"t'en", 'temps', 'tant', 'tend', 'tends'},
        {"s'y", 'si', 'ci'},
        {'son', 'sont'},
        {'luance', 'nuance'},
        {'faire', 'fer'},
        {'pas', 'pa'},
        {'du', 'de le'},
        {'des', 'de les'},
        {'au', 'à le'},
        {'aux', 'à les'},
        {'tous', 'tout', 'touts'},
        {'toute', 'toutes'},
    ]

    def filter(self, t):
        return any(t.lower in reps for reps in self._rep_sets)

    def trans(self, t):
        for reps in self._rep_sets:
            if t.lower in reps:
                t.replace_keep_form(self._choose_other_in_set(t.lower, reps))


# Alain permute certains suffixes.
class _AlainAlgo(_TokenAlgo):
    _suffix_sets = [
        {'er', 'ez', 'é', 'és', 'ée', 'ées'},
        {'tail', 'taille', 'tails', 'tailles'},
        {'vail', 'vaille', 'vails', 'vailles'},
        {'bail', 'baille', 'bails', 'bailles'},
        {'ment', 'mant', 'ments', 'mants'},
        {'son', 'sont', 'sons', 'sonts'},
        {'ain', 'ein', 'ains', 'eins'},
        {'ance', 'ence', 'ances', 'ences'},
        {'ard', 'art', 'ards', 'arts'},
        {'al', 'ale', 'als'},
        {'aud', 'o'},
        {'el', 'els', 'elle', 'elles'},
        {'il', 'ils', 'ile', 'iles'},
        {'eux', 'eu', 'eus'},
        {'eur', 'eure', 'eures'},
        {'cide', 'side', 'cides', 'sides'},
        {'vore', 'vores', 'vaure', 'vaures'},
        {'ose', 'ause', 'oses', 'auses'},
        {'gramme', 'grame', 'gram', 'grammes', 'grames', 'grams'},
        {'gène', 'gêne', 'gene', 'gènes', 'gênes', 'genes'},
        {'logie', 'logies', 'logis', 'logy'},
        {'ible', 'ibles'},
        {'let', 'lait', 'laits', 'lais', 'laid', 'laids'},
        {'iste', 'istes', 'isse', 'isses'},
        {'able', 'abe', 'ables', 'abes'},
        {'eil', 'eils', 'eille', 'eilles'},
        {'port', 'porc'},
    ]

    @staticmethod
    def _find_suffixes(t):
        for suffixes in _AlainAlgo._suffix_sets:
            for suffix in suffixes:
                if len(t) > len(suffix) and t.lower.endswith(suffix):
                    return suffix, suffixes

    def filter(self, t):
        return self._find_suffixes(t) is not None

    def trans(self, t):
        suffix, suffixes = self._find_suffixes(t)
        rem_len = len(suffix)
        suffix = self._choose_other_in_set(suffix, suffixes)
        t.replace_suffix(suffix, rem_len)


# Nicole gère tout ce qui concerne la conjugaison des verbes du premier
# groupe.
#
# Nicole identifie d'abord si un jeton est un verbe du premier groupe
# conjugué. Si c'est le cas, elle modifie sa conjugaison pour une forme
# homophonique.
class _NicoleAlgo(_TokenAlgo):
    @staticmethod
    def _find_suffix(t):
        m = re.match(r'(.+?)(eais|eait|eaient|ais|ait|aient|e|es|ent)$',
                     t.lower)

        if not m:
            # Pas une forme dont Nicole s'occupe
            return

        if m.group(1) not in boomer_verbs._verb_er_prefixes:
            # Pas un verbe du premier groupe
            return

        return m.group(2)

    def filter(self, t):
        return self._find_suffix(t) is not None

    def trans(self, t):
        orig_suffix = self._find_suffix(t)
        present_suffixes = {'e', 'es', 'ent'}
        imperfect_suffixes = {'ais', 'ait', 'aient'}
        imperfect2_suffixes = {'eais', 'eait', 'eaient'}

        # L'ordre est important ici puisque certains items d'un ensemble
        # incluent des items d'un autre ensemble (`eais` inclut `ais`
        # par exemple).
        if orig_suffix in present_suffixes:
            suffix = self._choose_other_in_set(orig_suffix, present_suffixes)
        elif orig_suffix in imperfect_suffixes:
            suffix = self._choose_other_in_set(orig_suffix, imperfect_suffixes)
        elif orig_suffix in imperfect2_suffixes:
            suffix = self._choose_other_in_set(orig_suffix,
                                               imperfect2_suffixes)

        t.replace_suffix(suffix, len(orig_suffix))


# Serge remplace des formes contractées par leur forme longue.
class _SergeAlgo(_TokenAlgo):
    _reps = {
        "qu'": 'que ',
        "d'": 'de ',
        "l'": 'la ',
    }

    @staticmethod
    def _find_prefix(t):
        for prefix, rep in _SergeAlgo._reps.items():
            if t.lower.startswith(prefix):
                return prefix, rep

    def filter(self, t):
        return self._find_prefix(t) is not None

    def trans(self, t):
        prefix, rep = self._find_prefix(t)
        t.replace_prefix(rep, len(prefix))


# André fait commencer certains mots par une majuscule.
class _AndréAlgo(_TokenAlgo):
    def filter(self, t):
        return len(t) >= 2 and t.starts_with_lower

    def trans(self, t):
        t.text = f'{t[0].upper()}{t[1:]}'


# Muriel fait commencer certains mots par une minuscule.
class _MurielAlgo(_TokenAlgo):
    def filter(self, t):
        return len(t) >= 2 and t.starts_with_upper

    def trans(self, t):
        t.text = f'{t[0].lower()}{t[1:]}'


# Denis allonge certaines ponctuations.
class _DenisAlgo(_TokenAlgo):
    def filter(self, t):
        return t.text in ('.', ',', '!', '?')

    def trans(self, t):
        output = []

        for _ in range(random.randint(2, 7)):
            if random.randint(0, 2) == 0:
                output.append(' ')

            output.append(t.text)

        t.text = ''.join(output)


# Guy supprime des accents.
class _GuyAlgo(_TokenAlgo):
    _accents = {
        'à': 'a',
        'â': 'a',
        'è': 'e',
        'é': 'e',
        'ê': 'e',
        'ë': 'e',
        'ï': 'i',
        'ö': 'o',
        'ô': 'o',
        'ù': 'u',
        'ü': 'u',
        'ç': 'c',
    }

    def filter(self, t):
        return any([c in self._accents for c in t.lower])

    def trans_cb(t):
        output = []

        for c in t.text:
            cl = c.lower()

            if cl in self._accents and _random_bool(self._true_false_weights):
                c_rep = self._accents[cl]

                if c.isupper():
                    c_rep = c_rep.upper()

                output.append(c_rep)
            else:
                output.append(c)

        t.text = ''.join(output)

    def process_tokens(self, tokens):
        self._apply_with_prob(tokens, [1, 0])


# Chantal remplace les apostrophes et les traits d'union par des espaces
# ou par rien.
class _ChantalAlgo(_TokenAlgo):
    def filter(self, t):
        return "'" in t or '-' in t

    def trans(self, t):
        t.text = t.text.replace("'", random.choice([' ', '']))
        t.text = t.text.replace("-", random.choice([' ', '']))


# Marc supprime des petits mots.
class _MarcAlgo(_TokenAlgo):
    _words = {
        'au',
        'ça',
        'ce',
        'ci',
        'du',
        'dû',
        'en',
        'es',
        'et',
        'eu',
        'il',
        'je',
        'la',
        'là',
        'le',
        'ma',
        'me',
        'ne',
        'ni',
        'on',
        'ou',
        'où',
        'pu',
        'sa',
        'se',
        'si',
        'ta',
        'te',
        'un',
    }

    def filter(self, t):
        return t.lower in self._words

    def trans(self, t):
        t.text = ''
        t.has_trailing_space = False


# Manon permute deux lettres d'un mot assez long.
class _ManonAlgo(_TokenAlgo):
    def filter(self, t):
        return len(t) >= 7

    def trans(self, t):
        first_index = random.randint(1, len(t) - 3)
        first_c = t[first_index]
        second_c = t[first_index + 1]
        t.text = f'{t.text[:first_index]}{second_c}{first_c}{t.text[first_index + 2:]}'


# Sylvain multiplie les espaces.
class _SylvainAlgo(_TextAlgo):
    def process_text(self, text):
        output = []

        for c in text:
            if c == ' ':
                if self._random_bool(self._true_false_weights):
                    output.append(' ' * random.randint(2, 3))
                    continue

            output.append(c)

        return ''.join(output)


# Josey ajoute des virgules ou des points.
class _JoseyAlgo(_TextAlgo):
    def process_text(self, text):
        output = []

        for c in text:
            output.append(c)

            if self._random_bool(self._true_false_weights):
                output.append(random.choice([',', '.']))

        return ''.join(output)


# Yves remplace bêtement certaines chaines par d'autres qui sont
# phonétiquement équivalentes.
class _YvesAlgo(_TextAlgo):
    _reps = {
        'ç': 'ss',
        'nn': 'n',
        'tt': 't',
        'ss': 'c',
    }

    def process_text(self, text):
        output = []
        i = 0

        while i < len(text):
            skip = False

            for src, dst in self._reps.items():
                if text[i:].startswith(src) and self._random_bool(self._true_false_weights):
                    output.append(dst)
                    i += len(src)
                    skip = True
                    break

            if skip:
                continue

            output.append(text[i])
            i += 1

        return ''.join(output)


def _tokenize(text):
    # Espaces en premier
    ttokens = text.split(' ')
    tokens = []

    # Ponctuations
    for tt in ttokens:
        m = re.match(r'(.+)([,.:;!?\])}]+)$', tt)

        if m:
            tokens.append(_Token(m.group(1), False))
            tokens.append(_Token(m.group(2), True))
        else:
            tokens.append(_Token(tt, True))

    return tokens


def _textize(tokens):
    ttokens = []

    for t in tokens:
        ttokens.append(t.text)

        if t.has_trailing_space:
            ttokens.append(' ')

    return ''.join(ttokens).strip()


def _retokenize_and_process(tokens, algo):
    text = _textize(tokens)
    tokens.clear()
    tokens += _tokenize(text)
    algo.process_tokens(tokens)


def _default_algo_cfgs():
    return {
        'monique': [3, 2],
        'alain': [2, 1],
        'nicole': [3, 1],
        'serge': [2, 1],
        'andré': [1, 3],
        'muriel': [1, 2],
        'denis': [2, 1],
        'guy': [1, 1],
        'chantal': [2, 1],
        'marc': [1, 5],
        'manon': [1, 3],
        'sylvain': [1, 7],
        'josey': [1, 15],
        'yves': [1, 3],
    }


def boomer(input, algo_cfgs=None, seed=None):
    # Grainer le générateur de nombres aléatoires
    if seed is not None:
        rand_state = random.getstate()
        random.seed(seed)

    # Diviser en jetons initialement
    tokens = _tokenize(input)

    # Configurer
    effective_algo_cfgs = _default_algo_cfgs()

    if algo_cfgs is not None:
        effective_algo_cfgs.update(algo_cfgs)

    # Construire les algorithmes sophistiqués
    algo_clss = [
        ('monique', _MoniqueAlgo),
        ('alain', _AlainAlgo),
        ('nicole', _NicoleAlgo),
        ('serge', _SergeAlgo),
        ('andré', _AndréAlgo),
        ('muriel', _MurielAlgo),
        ('denis', _DenisAlgo),
        ('guy', _GuyAlgo),
        ('chantal', _ChantalAlgo),
        ('marc', _MarcAlgo),
        ('manon', _ManonAlgo),
        ('sylvain', _SylvainAlgo),
        ('josey', _JoseyAlgo),
        ('yves', _YvesAlgo),
    ]
    algos = []

    for algo_name, algo_cls in algo_clss:
        algo_cfg = effective_algo_cfgs[algo_name]

        if algo_cfg is None:
            continue

        algos.append(algo_cls(algo_cfg))

    # Appliquer les transformations par jeton
    for algo in algos:
        if isinstance(algo, _TokenAlgo):
            _retokenize_and_process(tokens, algo)

    # Retour en texte
    output = _textize(tokens)

    # Quelques autres transformations applicables sur le texte complet
    for algo in algos:
        if isinstance(algo, _TextAlgo):
            output = algo.process_text(output)

    # Dégrainer le générateur de nombres aléatoires
    if seed is not None:
        random.setstate(rand_state)

    # Chow!
    return output
