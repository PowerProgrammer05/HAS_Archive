package Bank_Sim;
import java.util.ArrayList;
import Bank_Sim.Agent.*;
import org.json.simple.JSONObject;

public class Households{
    ArrayList<Household> households = new ArrayList<Household>();
    public JSONObject newBank(Household newHousehold){
        //id of newhousehold doesn't matter,
        // all new banks should be checked by this method
        JSONObject j = new JSONObject();

        if (households.isEmpty())
            newHousehold.id = 500;
        else
            newHousehold.id = households.get(households.size() - 1).id + 1; //Auto incrementing id

        if (newHousehold.id <= 1000) { //1000 is a limit
            j.put("Success", true);
            households.add(newHousehold);
        }
        else{
            j.put("Success", false);
            j.put("Message", "Maximum Household Number reached.");
        }
        return j;
    }
}

class Household extends Agent{
    float total_money = 100000000000000F; //$
    ArrayList<float[]> relations = new ArrayList<float[]>(); //{{Agent_id, 빌린값, 빌려준값}}

    Household (String name) {
        super(-1, name);
    }

    Household (int id, String name){
        super(id, name);
    }

    Household (String name, float total_money){
        super(-1, name, total_money);
    }

    Household (int id, String name, float total_money){
        super(id, name, total_money);
    }
}
