import numpy as np 
from nltk.sentiment import SentimentIntensityAnalyzer
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection, angle_between

import gensim.downloader
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity
glove_vectors = gensim.downloader.load('glove-twitter-25')

#sentiment
sia = SentimentIntensityAnalyzer()

def physical_step(npc):
    steps_per_sec = 30
    
    awake_time = 3000*steps_per_sec
    feed_interval_time = 1200*steps_per_sec
    feed_interval_time = 200*steps_per_sec
    amuse_time = 2000*steps_per_sec
    
    #physical_state tired hunger amusement work  
    #tired function 
    if npc.activity_flag != 1:
        npc.physical_state[0] += 1/awake_time
        if npc.physical_state[0] > 0.85:
            npc.physical_state[0] += npc.physical_state[0]*1/(2*awake_time)
    else:
        if npc.physical_state[0] > 0:
            npc.physical_state[0] -= 2/awake_time
        else:
            npc.physical_state[0] = 0
            
    #hunger function 
    if npc.activity_flag != 1:
        if npc.activity_flag == 3:
            npc.physical_state[1] -= 20/feed_interval_time 
            npc.physical_state[1] = max([npc.physical_state[1],0])
        else:
            npc.physical_state[1] += 1/feed_interval_time   
    else:
        npc.physical_state[1] += 0.4/feed_interval_time
        
    #amusement function
    if npc.activity_flag in [1,2] or npc.conv_flag == 1:
        npc.physical_state[2] = 0
    elif npc.activity_flag == 3:
        npc.physical_state[2] = min([npc.physical_state[2],0.4])
    else:
        npc.physical_state[2] += 1/amuse_time
        
def emotion_step(npc):
    steps_per_sec = 30
    step_val = 500
    #prev emotion_state 
    prev_emotion_state = npc.emotion_state
    #update based on physical state 
    comfort_state = 2*((1 - npc.physical_state[0])**2)*(1 - npc.physical_state[1])*(0.5 + 0.5*(1 - npc.physical_state[2])) - 1
    interest_state = 0
    #anger dropoff step step 
    if npc.emotion_state[2] != 0.0:
        if abs(npc.emotion_state[2]) < 0.01:
            npc.emotion_state[2] = 0.0
        else:
            npc.emotion_state[2] = 0.7*npc.emotion_state[2]
            
    #emotional state happy/sad calm/angry love/hate interest/bored
    npc.emotion_state[0] = comfort_state
    print('emote state ', npc.emotional_state)
    
def conv_step(npc):
    if npc.conv_input_phrase != None:
        #get the sentiment of the phrase
        input_phrase_sentiment = sia.polarity_scores(npc.conv_input_phrase)['compound']
        #get the conv options
        conv_text_options = npc.get_conv_options()
        #get the subject of the phrase 
        print('conv snetiment ', input_phrase_sentiment)
        #get the similarities between options 
        sim_list = conv_emb_match(npc.conv_input_phrase, conv_text_options)
        #get the similarities between sentiment 
        sent_list = sent_match(input_phrase_sentiment, conv_text_options)
        #get the match based on the combonation 
        print(sent_list)
        print(sim_list)
        match_list = list(np.array(sim_list)*np.array(sent_list))
        print('match list', match_list)
        print(max(match_list))
        match_ind = match_list.index(max(match_list))
        
        return conv_text_options[match_ind][0]
        

def conv_emb_match(input_phrase, conv_text_options):
    #get the input_phase embedding 
    input_phrase_vec = phrase_emb(input_phrase)
    #match to the cosine similarity of the vectors of the options 
    similar_list = []
    for conv_text in conv_text_options:
        conv_text_vec = phrase_emb(conv_text[0])
        input_phrase_vec = input_phrase_vec.reshape(1, -1)
        conv_text_vec = conv_text_vec.reshape(1, -1)
        similar_list.append(cosine_similarity(input_phrase_vec, conv_text_vec)[0][0])
    
    return similar_list
  
def phrase_emb(phrase):
    phrase_tokens = word_tokenize(phrase.lower())
    #get the summary of the token vectors 
    print(phrase)
    for token in phrase_tokens:
        try:
            phrase_vec += glove_vectors.get_vector(token.lower())
            #print('qqw1', token)
        except:
            phrase_vec = glove_vectors.get_vector(token.lower())
    return phrase_vec

def sent_match(phrase_sent, conv_text_options):
    #get the sentiment matches 
    sent_match_list = []
    for conv_text in conv_text_options:
        sent_match_list.append(1 - abs(phrase_sent - conv_text[1]))
    return sent_match_list

def goal_selection(npc):   
    print('ps',npc.physical_state, npc.change_action_prob)
    if npc.change_action_prob != None:
        prob_val = npc.change_action_prob
    else:
        prob_val = 1

    prob1 = prob_val + np.random.uniform(-0.05,0.05)
    prob2 = prob_val + np.random.uniform(-0.05,0.05)
    prob3 = prob_val + np.random.uniform(-0.05,0.05)
    if npc.physical_state[0] > prob1 and npc.activity_flag != 1:
        #go to sleep 
        action = 1
    elif npc.physical_state[1] > prob2 and npc.activity_flag != 3:
        #eat 
        action = 3
    elif npc.physical_state[1] > prob3:
        action = 2
    else:
        action = 4
    return action

def move_selection(npc, target_obj, goal, min_angle_val = 0.02):
    npc.move_keys = [0,0,0,0]
    npc.action_keys = [0,0,0]
    npc.activity_flag = 0
    if npc.contact_flag_obj != None:
        if target_obj in npc.contact_flag_obj.planet_obj_list:
            #get the rel pos for npc
            npc_dist_vec = npc.contact_flag_obj.pos - npc.pos
            npc_dist = absval(npc_dist_vec)      
            npc.npc_dist_vec = npc_dist_vec
            #check if contacting planet 
            npc_dist_pol = cart2pol(npc_dist_vec[0], npc_dist_vec[1])
            
            #get rel distance for each and 
            rel_dist = np.array(npc_dist_pol) - np.array([target_obj.rel_pos[0], target_obj.rel_pos[1] + np.pi])
            
            #move in the direction of target 
            rel_angle_dist = rel_dist[1] % (2*np.pi)
            if rel_angle_dist < np.pi and rel_angle_dist > min_angle_val:
                npc.move_keys[0] = 1
            elif rel_angle_dist > np.pi and rel_angle_dist < (2*np.pi - min_angle_val):
                npc.move_keys[1] = 1
            elif npc.inside_flag == 0:
                #act 
                npc.action_keys[0] = 1
            else:
                npc.activity_flag = goal
            
            #if inside other room then get outside 
            if npc.inside_flag == 1 and min_angle_val < rel_angle_dist < (2*np.pi - min_angle_val):
                npc.action_keys[0] = 1
                print(npc.action_keys, npc.prev_action_keys, npc.inside_flag, npc.prev_inside_flag)
        else:
            pass

def heuristic_step(npc):

    #select probs
    print(npc.move_keys, sum(npc.move_keys), npc.action_keys, sum(npc.action_keys))
    if sum(npc.move_keys) == 0 and sum(npc.action_keys) == 0:
        npc.change_action_prob = np.random.uniform(0.7,1)
        npc.end_action_prob = np.random.uniform(0,0.6)

    #get goal
    goal_action = goal_selection(npc)
       
    # null 0 sleep 1 rest 2 eat 3 work 4
    if npc.activity_flag != 0:
        print('activity flag ',npc.activity_flag)
        #get the probability of a reset
        reset_prob_val = npc.end_action_prob
        if npc.activity_flag == 3:
            move_selection(npc, npc.home, 3)
            if reset_prob_val > npc.physical_state[1]:
                npc.activity_flag = 0
        elif npc.activity_flag == 1:
            move_selection(npc, npc.home, 3)
            if reset_prob_val > npc.physical_state[0]:
                npc.activity_flag = 0
        elif npc.activity_flag == 4:
            move_selection(npc, npc.work, 4)
            npc.activity_flag = 0
    else:    
        # null 0 sleep 1 rest 2 eat 3 work 4
        if goal_action in [3, 1]:
            #go to home 
            print('npc indside flag ', npc.inside_flag, npc.action_keys)
            target = npc.home
            move_selection(npc, target, goal_action)
            print('move keys ', npc.move_keys)
            
        if goal_action in [4]:
            #go to work
            target = npc.work_location
            move_selection(npc, target, goal_action)
            print('move keys ', npc.move_keys)
                
    