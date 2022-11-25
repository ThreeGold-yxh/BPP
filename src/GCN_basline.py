import time
import torch
import torch.optim as optim
import torch.nn.functional as F
from dhg import Graph, Hypergraph
from dhg.models import GCN


from data_loader_tmp_copy import Database


def train(net_model: torch.nn.Module, nodes_features: torch.Tensor, graph: Graph, labels: torch.Tensor,
          train_idx: list[bool],
          optimizer: optim.Adam, epoch: int):
    net_model.train()

    st = time.time()
    optimizer.zero_grad()
    outs = net_model(nodes_features, graph)
    # outs: torch.Size([7403, 2000]) 就是7403个点，每个点有 2000个 features
    # labels: torch.Size([7403, 2000]) 就是7403个点，和每个点的真实的 2000个 features
    outs, labels = outs[train_idx], labels[train_idx]
    loss = F.cross_entropy(outs, labels)
    loss.backward()
    optimizer.step()
    print(f"Epoch: {epoch}, Time: {time.time() - st:.5f}s, Loss: {loss.item():.5f}")
    return loss.item()





@torch.no_grad()
def infer(net, nodes_features, graph, labels, idx, evaluator, test=False):
    net.eval()
    outs = net(nodes_features, graph)
    outs, labels = outs[idx], labels[idx]
    if not test:
        res = evaluator.validate(labels, outs)
    else:
        res = evaluator.test(labels, outs)
    return res

if __name__ == '__main__':
    # set device
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    # initialize the data_loader
    data_loader = Database("Disease", "attribute prediction dataset")

    # get the labels - the original nodes features
    labels = torch.FloatTensor(data_loader["raw_nodes_features"])

    # get the train,val,test nodes features
    train_nodes_features = torch.FloatTensor(data_loader["train_nodes_features"])
    validation_nodes_features = torch.FloatTensor(data_loader["validation_nodes_features"])
    test_nodes_features = torch.FloatTensor(data_loader["test_nodes_features"])

    # get train, validation, test mask to track the nodes
    train_mask = data_loader["train_node_mask"]
    val_mask = data_loader["val_node_mask"]
    test_mask = data_loader["test_node_mask"]

    # get the total number of nodes of this graph
    num_of_nodes: int = data_loader["num_nodes"]

    # generate the relationship between hyper edge and nodes
    # ex. [[1,2,3,4], [3,4], [9,7,4]...] where [1,2,3,4] represent a hyper edge
    hyper_edge_list = data_loader["edge_list"]

    # the hyper graph
    hyper_graph = Hypergraph(num_of_nodes, hyper_edge_list)

    # generate graph based on hyper graph
    graph = Graph.from_hypergraph_clique(hyper_graph, weighted=True)

    # the GCN model
    net_model = GCN(data_loader["num_features"], 32, data_loader["num_features"], use_bn=True)

    # set the optimizer
    optimizer = optim.Adam(net_model.parameters(), lr=0.01, weight_decay=5e-4)

    # set the device
    train_nodes_features, labels = train_nodes_features.to(device), labels.to(device)
    graph = graph.to(device)
    net_model = net_model.to(device)


    # start to train
    for epoch in range(200):
        # train
        # call the train method
        train(net_model, train_nodes_features, graph, labels, train_mask, optimizer, epoch)

        # if epoch % 1 == 0:
        #     with torch.no_grad():



