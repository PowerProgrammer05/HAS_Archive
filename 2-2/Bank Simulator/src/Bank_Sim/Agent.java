package Bank_Sim;

public class Agent {
    String name;
    int id;
    float total_money = 1000000F;

    Agent(int id){
        this.id = id;
    }
    Agent(int id, String name){
        this.id = id;
        this.name = name;
    }

    Agent(int id, String name, float total_money){
        this.id = id;
        this.name = name;
        this.total_money = total_money;
    }
}
