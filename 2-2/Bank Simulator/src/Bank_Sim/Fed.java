package Bank_Sim;
import org.json.simple.JSONObject;
import Bank_Sim.Banks.*;
import Bank_Sim.Households.*;
import Bank_Sim.Agent.*;

import java.util.ArrayList;

public class Fed extends Agent{
    float dRate = 0.04F; //Discount Rate, 0 <= <= 1
    float rRatio = 0.03F; //Reserve Ratio, 0  <= <= 1
    ArrayList<float[]> relations = new ArrayList<float[]>(); //{{Agent_id, 빌린값, 빌려준값}}

    Fed(){
        super(0, "Fed", 6587000000000F); //Only one fed instance can exist.
    }

    JSONObject changeRR(float newRR) {
        JSONObject jO = new JSONObject();
        if (newRR >= 0 || newRR <= 1) {
            jO.put("Success", true);
            jO.put("Message", "Reserve Ratio updated succesfully.");
            rRatio = newRR;
        }
        else{
            jO.put("Success", false);
            jO.put("Message", "Invalid Reserve Ratio.");
        }
        return jO;
    } //Changing reserve ratio

    JSONObject changeDR(float newDR) {
        JSONObject jO = new JSONObject();
        if (newDR >= 0 || newDR <= 1) {
            jO.put("Success", true);
            jO.put("Message", "Discount Rate updated succesfully.");
            dRate = newDR;
        }
        else{
            jO.put("Success", false);
            jO.put("Message", "Invalid Discount Rate.");
        }

        return jO;
    } //Changing discount rate
}

class FedUtils{
    JSONObject lendToBank(float amount, Fed fed, Bank bank) {
        JSONObject j = new JSONObject();
        if (amount <= 0){
            j.put("Message", "Not enough money in household.");
            j.put("Success", false);
            return j;
        }

        boolean fed_exist = true;
        for (int i = 0; i < fed.relations.size(); i++) {
            if (fed.relations.get(i)[0] == bank.id) {
                fed.relations.get(i)[2] += amount;
                fed_exist = false;
            }
        }

        boolean bank_exist = true;
        for (int i = 0; i < bank.relations.size(); i++) {
            if (bank.relations.get(i)[0] == fed.id){
                bank.relations.get(i)[1] += amount;
                bank_exist = false;
            }
        }

        if (fed_exist){
            float[] info = {bank.id, 0F, amount};
            fed.relations.add(info);
        }

        if (bank_exist) {
            float[] info2 = {fed.id, amount, 0F};
            bank.relations.add(info2);
        }

        bank.reserve += amount;
        fed.total_money -= amount;

        j.put("Message", "Succesfully borrowd from Fed.");
        j.put("Success", true);
        return j;
    }

    JSONObject repayFromBank(float amount, Fed fed, Bank bank) {
        JSONObject j = new JSONObject();
        if (amount <= 0){
            j.put("Message", "Not enough money in household.");
            j.put("Success", false);
            return j;
        }

        for (int i = 0; i < fed.relations.size(); i++) {
            if (fed.relations.get(i)[0] == bank.id)
                fed.relations.get(i)[2] -= amount;
        }

        for (int i = 0; i < bank.relations.size(); i++) {
            if (bank.relations.get(i)[0] == fed.id)
                bank.relations.get(i)[1] -= amount;
        }

        bank.reserve -= amount;
        fed.total_money += amount;

        j.put("Message", "Succesfully borrowd from Fed.");
        j.put("Success", true);
        return j;
    }
}

