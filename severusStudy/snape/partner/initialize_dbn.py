import pyAgrum as gum
# This PM is more sensitive to the feedback than to the prior -> It adapts faster, but is more inconsistent as well

def initialize_dbn():
    # hard coded BN
    pm = gum.BayesNet()
    e_0 = pm.add(gum.LabelizedVariable('e_0', 'Expertise_0', ['low', 'medium', 'high']))
    a_0 = pm.add(gum.LabelizedVariable('a_0', 'Attentiveness_0', ['low', 'medium', 'high']))
    c_0 = pm.add(gum.LabelizedVariable('c_0', 'Cooperativeness_0', ['low', 'medium', 'high']))
    l_0 = pm.add(gum.LabelizedVariable('l_0', 'CognitiveLoad_0', ['low', 'medium', 'high']))
    pos_0 = pm.add(gum.LabelizedVariable('pos_0', 'positive_0', ['yes', 'no']))
    neg_0 = pm.add(gum.LabelizedVariable('neg_0', 'negative_0', ['yes', 'no']))
    sub_0 = pm.add(gum.LabelizedVariable('sub_0', 'substantive_0', ['yes', 'no']))
    # time per sign and deletion rate is either lower or higher than current threshold or not existant
    tae_0 = pm.add(gum.LabelizedVariable('tae_0', 'timeanderror_0', ['lower', 'higher', 'None']))
    e_t = pm.add(gum.LabelizedVariable('e_t', 'Expertise_t', ['low', 'medium', 'high']))
    a_t = pm.add(gum.LabelizedVariable('a_t', 'Attentiveness_t', ['low', 'medium', 'high']))
    c_t = pm.add(gum.LabelizedVariable('c_t', 'Cooperativeness_t', ['low', 'medium', 'high']))
    l_t = pm.add(gum.LabelizedVariable('l_t', 'CognitiveLoad_t', ['low', 'medium', 'high']))
    pos_t = pm.add(gum.LabelizedVariable('pos_t', 'positive_t', ['yes', 'no']))
    neg_t = pm.add(gum.LabelizedVariable('neg_t', 'negative_t', ['yes', 'no']))
    sub_t = pm.add(gum.LabelizedVariable('sub_t', 'substantive_t', ['yes', 'no']))
    tae_t = pm.add(gum.LabelizedVariable('tae_t', 'timeanderror_t', ['lower', 'higher', 'None']))

    pm.addArc(pos_0, a_0)
    pm.addArc(neg_0, a_0)
    pm.addArc(c_0, a_0)
    pm.addArc(sub_0, c_0)
    pm.addArc(pos_0, e_0)
    pm.addArc(e_0, l_0)
    pm.addArc(tae_0, l_0)
    # transition
    pm.addArc(a_0, a_t)
    pm.addArc(c_0, c_t)
    pm.addArc(e_0, e_t)
    pm.addArc(l_0, l_t)
    # next layer
    pm.addArc(pos_t, a_t)
    pm.addArc(neg_t, a_t)
    pm.addArc(c_t, a_t)
    pm.addArc(sub_t, c_t)
    pm.addArc(pos_t, e_t)
    pm.addArc(e_t, l_t)
    pm.addArc(tae_t, l_t)

    # Expertise initial
    pm.cpt('pos_0').fillWith([0.5, 0.5])
    pm.cpt('neg_0').fillWith([0.5, 0.5])
    pm.cpt('sub_0').fillWith([0.5, 0.5])
    pm.cpt('tae_0').fillWith([0.3, 0.4, 0.3])

    pm.cpt('a_0')[{'c_0':0, 'pos_0': 1, 'neg_0': 1}] = [0.8, 0.15, 0.05]
    pm.cpt('a_0')[{'c_0':0,'pos_0': 0, 'neg_0': 1}] = [0.2, 0.3, 0.5]
    pm.cpt('a_0')[{'c_0':0,'pos_0': 1, 'neg_0': 0}] = [0.2, 0.3, 0.5]
    
    pm.cpt('a_0')[{'c_0':1, 'pos_0': 1, 'neg_0': 1}] = [0.5, 0.4, 0.1]
    pm.cpt('a_0')[{'c_0':1,'pos_0': 0, 'neg_0': 1}] = [0.1, 0.4, 0.5]
    pm.cpt('a_0')[{'c_0':1,'pos_0': 1, 'neg_0': 0}] = [0.1, 0.4, 0.5]
    
    pm.cpt('a_0')[{'c_0':2, 'pos_0': 1, 'neg_0': 1}] = [0.6, 0.3, 0.1]
    pm.cpt('a_0')[{'c_0':2,'pos_0': 0, 'neg_0': 1}] = [0.05, 0.15, 0.8]
    pm.cpt('a_0')[{'c_0':2,'pos_0': 1, 'neg_0': 0}] = [0.05, 0.15, 0.8]

    # Cooperativeness initial
    pm.cpt('c_0')[{'sub_0': 1}] = [0.85, 0.1, 0.05]
    pm.cpt('c_0')[{'sub_0': 0}] = [0.05, 0.1, 0.85]

    # Expertise initial
    pm.cpt('e_0')[{'pos_0': 1}] = [0.8, 0.019, 0.001]
    pm.cpt('e_0')[{'pos_0': 0}] = [0.001, 0.199, 0.8]

    # Cognitive Load initial
    pm.cpt('l_0')[{'e_0': 0, 'tae_0': 0}] = [0.25, 0.5, 0.25]
    pm.cpt('l_0')[{'e_0': 1, 'tae_0': 0}] = [0.45, 0.35, 0.2]
    pm.cpt('l_0')[{'e_0': 2, 'tae_0': 0}] = [0.75, 0.2, 0.05]

    pm.cpt('l_0')[{'e_0': 0, 'tae_0': 1}] = [0.001, 0.099, 0.9]
    pm.cpt('l_0')[{'e_0': 1, 'tae_0': 1}] = [0.001, 0.299, 0.7]
    pm.cpt('l_0')[{'e_0': 2, 'tae_0': 1}] = [0.1, 0.4, 0.5]

    # Cognitive Load initial
    pm.cpt('l_0')[{'e_0': 0, 'tae_0': 2}] = [0.05, 0.1, 0.85]
    pm.cpt('l_0')[{'e_0': 1, 'tae_0': 2}] = [0.15, 0.7, 0.15]
    pm.cpt('l_0')[{'e_0': 2, 'tae_0': 2}] = [0.85, 0.1, 0.05]

    # Expertise next, conditioned on both e_0 and pos_t
    pm.cpt('e_t')[{'e_0': 0, 'pos_t': 1}] = [0.9, 0.09,0.01]  # If no positive feedback, expertise likely remains low
    pm.cpt('e_t')[{'e_0': 0, 'pos_t': 0}] = [0.3, 0.5, 0.2]  # With positive feedback, some chance of improving

    pm.cpt('e_t')[{'e_0': 1, 'pos_t': 1}] = [0.25, 0.7, 0.05]  # Expertise likely remains the same without feedback
    pm.cpt('e_t')[{'e_0': 1, 'pos_t': 0}] = [0.05, 0.35, 0.6]  # Expertise improvement more likely with feedback

    pm.cpt('e_t')[{'e_0': 2, 'pos_t': 1}] = [0.001, 0.149, 0.85]  # Without feedback, expertise unlikely to drop much
    pm.cpt('e_t')[{'e_0': 2, 'pos_t': 0}] = [0.0001, 0.0199, 0.98]  # With feedback, expertise is more stable

    # Cooperativeness next
    pm.cpt('c_t')[{'c_0': 0, 'sub_t': 1}] = [0.85, 0.1, 0.05]
    pm.cpt('c_t')[{'c_0': 1, 'sub_t': 1}] = [0.1, 0.85, 0.05]
    pm.cpt('c_t')[{'c_0': 2, 'sub_t': 1}] = [0.05, 0.1, 0.85]

    pm.cpt('c_t')[{'c_0': 0, 'sub_t': 0}] = [0.3, 0.55, 0.15]
    pm.cpt('c_t')[{'c_0': 1, 'sub_t': 0}] = [0.05, 0.35, 0.6]
    pm.cpt('c_t')[{'c_0': 2, 'sub_t': 0}] = [0.01, 0.04, 0.95]

    # Cognitive Load next
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 0, 'tae_t': 0}] = [0.8, 0.199, 0.001]
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 1, 'tae_t': 0}] = [0.3, 0.6, 0.1]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 0, 'tae_t': 0}] = [0.9, 0.099, 0.001]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 1, 'tae_t': 0}] = [0.3, 0.65, 0.05]
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 2, 'tae_t': 0}] = [0.1, 0.25, 0.65]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 0, 'tae_t': 0}] = [0.995, 0.004, 0.001]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 2, 'tae_t': 0}] = [0.45, 0.35, 0.2]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 1, 'tae_t': 0}] = [0.6, 0.399, 0.001]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 2, 'tae_t': 0}] = [0.15, 0.4, 0.45]

    pm.cpt('l_t')[{'e_t': 0, 'l_0': 0, 'tae_t': 1}] = [0.5, 0.3, 0.2]
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 1, 'tae_t': 1}] = [0.001, 0.599, 0.4]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 0, 'tae_t': 1}] = [0.7, 0.2, 0.1]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 1, 'tae_t': 1}] = [0.1, 0.65, 0.25]
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 2, 'tae_t': 1}] = [0.05, 0.15, 0.8]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 0, 'tae_t': 1}] = [0.85, 0.1, 0.05]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 2, 'tae_t': 1}] = [0.2, 0.35, 0.45]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 1, 'tae_t': 1}] = [0.1, 0.7, 0.2]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 2, 'tae_t': 1}] = [0.001, 0.349, 0.65]

    pm.cpt('l_t')[{'e_t': 0, 'l_0': 0, 'tae_t': 2}] = [0.8, 0.15, 0.05]
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 1, 'tae_t': 2}] = [0.3, 0.6, 0.1]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 0, 'tae_t': 2}] = [0.9, 0.09, 0.01]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 1, 'tae_t': 2}] = [0.1, 0.8, 0.1]
    pm.cpt('l_t')[{'e_t': 0, 'l_0': 2, 'tae_t': 2}] = [0.01, 0.09, 0.9]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 0, 'tae_t': 2}] = [0.9, 0.09, 0.01]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 2, 'tae_t': 2}] = [0.33, 0.34, 0.33]
    pm.cpt('l_t')[{'e_t': 2, 'l_0': 1, 'tae_t': 2}] = [0.35, 0.6, 0.05]
    pm.cpt('l_t')[{'e_t': 1, 'l_0': 2, 'tae_t': 2}] = [0.05, 0.35, 0.6]

    #Attentiveness next
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 0, 'c_t':0}] = [0.9, 0.09, 0.01]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 0, 'c_t':0}] = [0.45, 0.45, 0.1]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 0, 'c_t':0}] = [0.45, 0.55, 0.1]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 1, 'c_t':0}] = [0.2, 0.799, 0.001]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 1, 'c_t':0}] = [0.1, 0.55, 0.35]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 1, 'c_t':0}] = [0.1, 0.55, 0.35]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 2, 'c_t':0}] = [0.05, 0.35, 0.6]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 2, 'c_t':0}] = [0.001, 0.099, 0.9]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 2, 'c_t':0}] = [0.001, 0.099, 0.9]

    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 0, 'c_t':1}] = [0.85, 0.1, 0.05]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 0, 'c_t':1}] = [0.4, 0.5, 0.1]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 0, 'c_t':1}] = [0.4, 0.5, 0.1]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 1, 'c_t':1}] = [0.1, 0.899, 0.001]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 1, 'c_t':1}] = [0.01, 0.59, 0.4]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 1, 'c_t':1}] = [0.01, 0.59, 0.4]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 2, 'c_t':1}] = [0.05, 0.25, 0.7]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 2, 'c_t':1}] = [0.001, 0.049, 0.95]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 2, 'c_t':1}] = [0.001, 0.049, 0.95]

    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 0, 'c_t':2}] = [0.8, 0.15, 0.05]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 0, 'c_t':2}] = [0.35, 0.55, 0.1]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 0, 'c_t':2}] = [0.35, 0.55, 0.1]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 1, 'c_t':2}] = [0.2, 0.7, 0.1]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 1, 'c_t':2}] = [0.01, 0.5, 0.49]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 1, 'c_t':2}] = [0.01, 0.5, 0.49]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 1, 'a_0': 2, 'c_t':2}] = [0.005, 0.2, 0.75]
    pm.cpt('a_t')[{'pos_t': 0, 'neg_t': 1, 'a_0': 2, 'c_t':2}] = [0.001, 0.009, 0.99]
    pm.cpt('a_t')[{'pos_t': 1, 'neg_t': 0, 'a_0': 2, 'c_t':2}] = [0.001, 0.009, 0.99]


    # Feedback next
    pm.cpt('pos_t').fillWith([0.01, 0.99])
    pm.cpt('neg_t').fillWith([0.01, 0.99])
    pm.cpt('sub_t').fillWith([0.01, 0.99])
    pm.cpt('tae_t').fillWith([0.1, 0.1, 0.8])

    return pm
