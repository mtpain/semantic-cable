import matplotlib.pyplot as plt
import networkx as nx

from collections import Counter
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

    return text_counts(
        get_iatv_corpus_doc_data(iatv_corpus_name, network, db_name=db_name),
        remove_commercials=remove_commercials
    )


def vis_graph(g, node_color='r', figsize=(10, 10)):

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    node_pos = nx.drawing.nx_pydot.graphviz_layout(g)
    label_pos = {
        k: array([v[0] + .1, v[1] + .01])
        for k, v in node_pos.items()
    }

    nx.draw_networkx_labels(g, pos=label_pos)
    nx.draw_networkx_nodes(g, node_color=node_color, pos=node_pos, alpha=0.5)
    nx.draw_networkx_edges(g, pos=node_pos, width=1.0)

    return fig, ax
