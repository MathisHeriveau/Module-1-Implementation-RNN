import numpy as np # Créer des Arrays 
import random # Pour l'apprentissage 
import os # Pour ecrire dans un fichier 
import torch
import torch.nn as nn # Neurone Network 
import torch.nn.functional as F # Fonction utile pour les neurones
import torch.optim as optim # Utile pour les gradient / optimiseur qui converge plus rapidement que gradient
import torch.autograd as autograd # Rétropropagation 
from torch.autograd import Variable # Permet la convertion 


# Creating the architecture of the Neural Network

class Network(nn.Module): # Permet de créé une ia avec nn
    
    def __init__(self, input_size, nb_action): 
        
        super(Network,self).__init__()
        
        self.input_size = input_size
        self.nb_action = nb_action
        
        # Création d'une couche caché 
        self.fc1 = nn.Linear(input_size, 32)
        self.fc2 = nn.Linear(32, nb_action)
        
    def forward(self, state):
        x = F.relu(self.fc1(state))
        q_values = self.fc2(x) 
        return q_values
        
# Implementing Experience Replay

class ReplayMemory(object):
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        
    def push(self, event): 
        self.memory.append(event)
        if len(self.memory) > self.capacity:
            del self.memory[0]
            
    def sample(self, batch_size): 
        samples = zip(*random.sample(self.memory, batch_size)) 
        
        return map(lambda x: Variable(torch.cat(x, dim=0)), samples)
    
# Implementing Deep Q-Learning algorithme     

class Dqn():
    
    def __init__(self, input_size, nb_action, gamma):
       
        self.model = Network(input_size, nb_action) 
        self.gamma = gamma
        self.reward_window = [] 
        self.memory = ReplayMemory(100_000)
        self.optimizer = optim.Adam(self.model.parameters(), lr = 0.0001)
        self.last_state = torch.Tensor(input_size).unsqueeze(0) 
        self.last_action = 0
        self.last_reward = 0
        self.temperature = 3

    def select_action(self, state) : 
        probs = F.softmax(self.model(state) * self.temperature, dim = 1)
        action = probs.multinomial(num_samples=1)
        return action.data[0,0]
    
    def learn(self, batch_state, batch_next_state, batch_reward, batch_action ):
        batch_action = batch_action.clamp(min=0, max=2).long()
        
        outputs = self.model(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)
        next_outputs = self.model(batch_next_state).detach().max(1)[0]
        targets = batch_reward + self.gamma * next_outputs
        td_loss = F.smooth_l1_loss(outputs, targets)
        self.optimizer.zero_grad()
        td_loss.backward()
        self.optimizer.step()

        
    def update(self, reward, new_signal):
        new_state = torch.Tensor(new_signal).float().unsqueeze(0)
        # Sauvegarder la transition
        self.memory.push((self.last_state, new_state, torch.LongTensor([int(self.last_action)]), torch.tensor([self.last_reward])))
        action = self.select_action(new_state)
        
        # Learn 
        if len(self.memory.memory)>100:
            batch_state, batch_next_state, batch_reward, batch_action = self.memory.sample(100)
            self.learn(batch_state, batch_next_state, batch_reward, batch_action)
        
        self.last_state = new_state
        self.last_action = action
        self.last_reward = reward
        
        self.reward_window.append(reward)
        if len(self.reward_window) > 1000:
            del self.reward_window[0]
        
        return action
        
    def score(self):  
        return sum(self.reward_window) / (len(self.reward_window) + 1.)
    
    def save(self):
        torch.save(
            {"state_dict": self.model.state_dict(),
             "optimizer": self.optimizer.state_dict()},
            "last_brain.pth"
            )
        
    def load(self):
        if os.path.isfile("last_brain.pth"):
        
            print ("=> loading checkpoint ...")
            checkpoint = torch.load("last_brain.pth")
            self.model.load_state_dict(checkpoint['state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            
            print ("done !")
        else:
            print ("no checkpoint found ...")
            
        
        
        
    
        

