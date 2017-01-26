import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import warnings

from collections import Counter, OrderedDict
from mongoengine import connect
from nltk.corpus import stopwords
from numpy import array


STOPWORDS = set(stopwords.words('english'))


def get_iatv_corpus_names(db_name='metacorps'):

    return [c['name'] for c in
            connect().get_database(
                    db_name
                ).get_collection(
                    'iatv_corpus'
                ).find()
            ]


def get_iatv_corpus_doc_data(iatv_corpus_name, network, db_name='metacorps'):

    db = connect().get_database(db_name)

    doc_ids = db.get_collection('iatv_corpus').find_one(
        {'name': iatv_corpus_name}
    )['documents']

    iatv_docs = db.get_collection('iatv_document')

    docs = [iatv_docs.find_one({'_id': doc_id})
            for doc_id in doc_ids]

    docs = [doc['document_data'] for doc in docs if doc['network'] == network]

    return docs


def text_counts(docs, remove_commercials=True):
    '''
    Make word count for list of documents
    '''
    if remove_commercials:
        texts = [[word.lower() for word in doc.split()
                  if word.isalpha()
                  and not any(c.islower() for c in word)
                  ]
                 for doc in docs]
    else:
        texts = [[word.lower() for word in doc.split()
                  if word.isalpha()
                  ]
                 for doc in docs]

    c = Counter([])
    for t in texts:
        c.update(t)
    # remove 1st word always 'transcript'; also lower now
    texts = [[word for word in text[1:]
              if c[word] >= 10 and word not in STOPWORDS]
             for text in texts]

    c = Counter([])
    for t in texts:
        c.update(t)

    return (texts, c)


def get_corpus_text(iatv_corpus_name, network, db_name='metacorps',
                    remove_commercials=True):

    return make_texts_list(
        get_iatv_corpus_doc_data(iatv_corpus_name, network, db_name=db_name),
        remove_commercials=remove_commercials
    )


def make_texts_list(docs, remove_commercials=True):
    '''
    Make texts lists for list of documents
    '''
    if remove_commercials:
        texts = [[word.lower() for word in doc.split()
                  if word.isalpha()
                  and not any(c.islower() for c in word)
                  ]
                 for doc in docs if len(doc) != 0]
    else:
        texts = [[word.lower() for word in doc.split()
                  if word.isalpha()
                  ]
                 for doc in docs]

    c = Counter([])
    for t in texts:
        c.update(t)
    # remove 1st word always 'transcript'; also lower now
    texts = [[word for word in text[1:]
              if c[word] >= 1 and word not in STOPWORDS]
             for text in texts]

    return texts


def make_doc_word_matrix(texts):

    c = OrderedCounter([])
    for t in texts:
        c.update(t)

    vocab = list(c.keys())
    n_words = len(vocab)
    n_docs = len(texts)
    doc_word_mat = np.zeros((n_docs, n_words), dtype=int)

    vocab_lookup = get_word_idx_lookup(vocab)

    for t_idx, t in enumerate(texts):
        c = Counter(t)
        for k, v in c.items():
            doc_word_mat[t_idx, vocab_lookup[k]] = v

    return (doc_word_mat, vocab)


def vis_graph(g, node_color='r', figsize=(10, 10),
              layout='graphviz', alpha=0.5):

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

    if layout == 'graphviz':
        node_pos = nx.drawing.nx_pydot.graphviz_layout(g)
    elif layout == 'circular':
        node_pos = nx.drawing.layout.circular_layout(g)
    elif layout == 'spectral':
        node_pos = nx.drawing.layout.spectral_layout(g)
    elif layout == 'spring':
        node_pos = nx.drawing.layout.spring_layout(g)
    elif layout == 'shell':
        node_pos = nx.drawing.layout.shell_layout(g)
    else:
        warnings.warn(
            'layout {} not found, defaulting to graphviz'.format(layout)
        )
        node_pos = nx.drawing.nx_pydot.graphviz_layout(g)

    if node_pos not in ['spring']:
        label_pos = {
            k: array([v[0] + .1, v[1] + .01])
            for k, v in node_pos.items()
        }

    nx.draw_networkx_labels(g, font_weight='bold', font_size=18, pos=label_pos)
    nx.draw_networkx_nodes(g, node_size=500,
                           node_color=node_color, pos=node_pos, alpha=alpha)
    nx.draw_networkx_edges(g, pos=node_pos, edge_color='grey', width=1.0)

    return fig, ax


# see https://docs.python.org/3.4/library/collections.html?highlight=ordereddict#ordereddict-examples-and-recipes
class OrderedCounter(Counter, OrderedDict):
    'Counter that remembers the order elements are first encountered'

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

    def __reduce__(self):
        return self.__class__, (OrderedDict(self),)


def get_word_idx_lookup(vocab):

    return dict((el, idx) for idx, el in enumerate(vocab))