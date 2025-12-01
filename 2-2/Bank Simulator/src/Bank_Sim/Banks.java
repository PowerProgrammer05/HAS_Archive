package Bank_Sim;
import java.util.ArrayList;
import org.json.simple.JSONObject; //message 송신과 success 여부를 위해 JSON을 사용함

public class Banks {
    ArrayList<Bank> banks = new ArrayList<Bank>();
    public JSONObject newBank(Bank newBank){
        //id of a new bank doesn't matter (as it is automatically assigned here)
        // all new banks should be checked by this method
        JSONObject j = new JSONObject();

        if (banks.isEmpty())
            newBank.id = 1;
        else
            newBank.id = banks.get(banks.size() - 1).id + 1; //Auto incrementing id

        if (newBank.id <= 500) { //500 is a limit of banks
            j.put("Success", true);
            banks.add(newBank);
        }
        else{
            j.put("Success", false);
            j.put("Message", "Maximum Bank Number reached.");
        }
        return j;
    }
}

class Bank extends Agent{
    //id is Auto incremented, <= 500
    String name;

    float reserve = 50000000000F; //$, default is $500B
    float loans = 0;  //$, default is $0
    float deposit = 50000000000F; //$, default is $500B
    float equity = 100000000000F; //$, default is $1000B
    float loanRate = 0.023F;
    float depositRate = 0.03F;
    float total_money = this.reserve + this.loans + this.deposit + this.equity;
    ArrayList<float[]> relations = new ArrayList<float[]>();  //{{Agent_id, 빌린값, 빌려준값}}

    Bank(String name){
        super(-1, name);
    }

    //Overloaded Constructors
    Bank(int id, String name){
        super(id, name);
    }

    Bank(String name, float reserve, float deposit, float equity){
            super(-1, name);
            this.reserve = reserve;
            this.deposit = deposit;
            this.equity = equity;
    }

    Bank(int id, String name, float reserve, float deposit, float equity){
        super(id, name);
        this.reserve = reserve;
        this.deposit = deposit;
        this.equity = equity;
    }

    Bank(String name, float total_money, float rRatio, float equity, String a){ //When reserve ratio is given, a is trash val
            super(-1, name);
            this.total_money = total_money;
            this.equity = equity;
            this.deposit = (1 / (1 + rRatio)) * (this.total_money - this.equity - this.loans);
            this.reserve = this.total_money - this.deposit - this.equity - this.loans;
    }

    Bank(int id, String name, float total_money, float rRatio, float equity, String a){ //When reserve ratio is given, a is trash val
        super(id, name);
        this.total_money = total_money;
        this.equity = equity;
        this.deposit = (1 / (1 + rRatio)) * (this.total_money - this.equity - this.loans);
        this.reserve = this.total_money - this.deposit - this.equity - this.loans;
    }

    public JSONObject updateRR(float rRatio){ //Updating Reserve Ratio (Automatically fits reserve ratio)
        this.reserve = (rRatio / (1 + rRatio)) * (this.total_money - this.equity - this.loans);
        this.equity = this.total_money - this.deposit - this.equity - this.loans - this.reserve;

        JSONObject j = new JSONObject();
        if (this.equity >= 0){
            j.put("Success", true);
            j.put("Message", "Bank Status Updated.");
            return j;
        }
        else {
            j.put("Success", false);
            j.put("Message", "Status update failed. Equity becomes minus");
            return j;
        }
    }

    public JSONObject minusEquity(){ //when equity is under zero
        JSONObject j = new JSONObject();
        if (this.equity < 0) {
            j.put("id", this.id);
        }
        return j;
    }

    public void bankrupt() { //when bank is bankrupt (파산, 모든 정보를 0으로)
        this.id = -2; // bankrupt id is -2

        this.reserve = 0F;
        this.loans = 0F;
        this.deposit = 0F;
        this.equity = 0F;
        this.total_money = 0F;
        this.relations.clear();
    }
}

class BankUtils{
    void deposit(float amount, Household house, Bank bank) { //deposit from households to bank
        boolean house_exist = true;
        for (int i = 0; i < house.relations.size(); i++) { //check if bank is already in householdsl relations list
            if (house.relations.get(i)[0] == bank.id) {
                house.relations.get(i)[2] += amount;
                house_exist = false;
            }
        }

        boolean bank_exist = true;
        for (int i = 0; i < bank.relations.size(); i++) {  //check if household is already in banks' relations list
            if (house.relations.get(i)[0] == house.id)
                house.relations.get(i)[1] += amount;
                bank_exist = false;
        }

        if (house_exist){ //Adding new id
            float[] info = {bank.id, 0F, amount};
            house.relations.add(info);
        }

        if (bank_exist) { //Adding new id
            float[] info2 = {house.id, amount, 0F};
            bank.relations.add(info2);
        }

        house.total_money -= amount;
        bank.total_money += amount;

        bank.reserve += amount;
        bank.deposit += amount;
    }

    void giveLoan(float amount, Household house, Bank bank) { //Loan from bank to households
        if (amount <= 0) return;
            if (bank.reserve < amount) return;

        //similar structure (deposit class)
        boolean house_exist = true;
        for (int i = 0; i < house.relations.size(); i++) {
            if (house.relations.get(i)[0] == bank.id) {
                house.relations.get(i)[1] += amount;
                house_exist = false;
            }
        }

        boolean bank_exist = true;
        for (int i = 0; i < bank.relations.size(); i++) {
            if (house.relations.get(i)[0] == house.id)
                house.relations.get(i)[2] += amount;
                bank_exist = false;
        }

        if (house_exist){
            float[] info = {bank.id, amount, 0F};
            house.relations.add(info);
        }

        if (bank_exist) {
            float[] info2 = {house.id, 0F, amount};
            bank.relations.add(info2);
        }

        house.total_money += amount;
        bank.total_money += amount;
        bank.reserve -= amount;
        bank.loans += amount;
    }

    JSONObject repayLoan(float amount, Household house, Bank bank) { //households repaying loans to bank
        JSONObject j = new JSONObject();

        //similar structure but doesn't have to add new id, because there must be an id if this function is called
        if (amount <= 0){
            j.put("Message", "Negative Amount");
            j.put("Success", false);
            return j;
        }
        if (house.total_money < amount) {
            j.put("Message", "Not enough money in household.");
            j.put("Success", false);
            return j;
        }

        bank.total_money += amount;
        bank.reserve += amount;
        house.total_money -= amount;

        for (int i = 0; i < house.relations.size(); i++) {
            if (house.relations.get(i)[0] == bank.id)
                house.relations.get(i)[1] -= amount;
        }

        for (int i = 0; i < bank.relations.size(); i++) {
            if (house.relations.get(i)[0] == house.id)
                house.relations.get(i)[2] -= amount;
        }

        j.put("Message", "Successfully repaid.");
        j.put("Success", true);

        return j;
    }


    JSONObject borrowFromBank(float amount, Bank lender, Bank borrower) { //a bank borrowing from another bank
        JSONObject j = new JSONObject();

        //also similar to repayLoan function
        if (amount <= 0){
            j.put("Message", "Negative Amount");
            j.put("Success", false);
            return j;
        }
        if (lender.total_money < amount) {
            j.put("Message", "Not enough money in lending bank.");
            j.put("Success", false);
            return j;
        }

        lender.loans -= amount;
        borrower.reserve += amount;

        lender.total_money -= amount;
        borrower.total_money += amount;

        boolean lend_exist = true;
        for (int i = 0; i < lender.relations.size(); i++) {
            if (lender.relations.get(i)[0] == borrower.id){
                lender.relations.get(i)[2] += amount;
                lend_exist = false;
            }
        }

        boolean borrow_exist = true;
        for (int i = 0; i < borrower.relations.size(); i++) {
            if (borrower.relations.get(i)[0] == lender.id){
                borrower.relations.get(i)[1] += amount;
                borrow_exist = false;
            }
        }

        if (lend_exist){
            float[] info = {borrower.id, 0F, amount};
            lender.relations.add(info);
        }

        if (borrow_exist){
            float[] info = {lender.id, amount, 0F};
            borrower.relations.add(info);
        }

        j.put("Message", "Successfully borrowed.");
        j.put("Success", true);

        return j;
    }
    JSONObject repayToBank(float amount, Bank lender, Bank borrower) { //Repaying to bank (After borrowing from another bank)
        JSONObject j = new JSONObject();

        //Also similar structrue
        if (amount <= 0){
            j.put("Message", "Negative Amount");
            j.put("Success", false);
            return j;
        }
        if (borrower.total_money < amount) {
            j.put("Message", "Not enough money in lending bank.");
            j.put("Success", false);
            return j;
        }

        lender.loans += amount;
        borrower.reserve -= amount;

        lender.total_money += amount;
        borrower.total_money -= amount;

        boolean lend_exist = true;
        for (int i = 0; i < lender.relations.size(); i++) {
            if (lender.relations.get(i)[0] == borrower.id){
                lender.relations.get(i)[2] += amount;
                lend_exist = false;
            }
        }

        boolean borrow_exist = true;
        for (int i = 0; i < borrower.relations.size(); i++) {
            if (borrower.relations.get(i)[0] == lender.id){
                borrower.relations.get(i)[1] += amount;
                borrow_exist = false;
            }
        }

        if (lend_exist){
            float[] info = {borrower.id, 0F, amount};
            lender.relations.add(info);
        }

        if (borrow_exist){
            float[] info = {lender.id, amount, 0F};
            borrower.relations.add(info);
        }

        j.put("Message", "Successfully repaid.");
        j.put("Success", true);

        return j;
    }

    void applyInterest(Bank bank, float loanRate, float depositRate) { //Applying interest rate in every timestamp (should be called every time)
        float income = bank.loans * loanRate;
        float expense = bank.deposit * depositRate;
        float net = income - expense;

        bank.reserve += net;
        bank.equity  += net;

        bank.total_money = bank.reserve + bank.loans + bank.deposit + bank.equity;
    }

    JSONObject checkReserveReq(Bank bank, float rRatio) { //Check if the bank meets reserve ratio (지급준비금 비율 만족하는지)
        JSONObject j = new JSONObject();
        float required = rRatio * bank.deposit;
        if (bank.reserve >= required) {
            j.put("Req", true);
            j.put("Message", "reserve over required");
        }
        else {
            j.put("Req", false);
            j.put("Message", "reserve lacks required");
        }
        return j;
    }

    JSONObject handleBankRun(Bank bank, float runRatio) { //runRatio는 예금 중 몇퍼 인출되는지, this method is a protocol for bankrun.
        JSONObject j = new JSONObject();
        if (runRatio <= 0f){
            j.put("Message", "run ratio is negative or zero");
        }
        if (runRatio > 1f) runRatio = 1f;
        float withdraw = bank.deposit * runRatio;

        if (bank.reserve >= withdraw) { //as reserve is larger than the amount people want to withdraw, the bank isn't bankrupt
            bank.reserve -= withdraw;
            bank.deposit -= withdraw;
            j.put("Message", "BankRun handled with reserve");
            return j;
        } else {
            float shortage = withdraw - bank.reserve;

            bank.reserve = 0f;
            bank.deposit -= withdraw;
            bank.equity  -= shortage;

            if (bank.equity < 0f) { //in this case, bankrun is out of banks' capability, so bank is bankrupt
                j.put("Message", bank.name + "bank couldn't handle the bankrun, so it is bankrupt,");
                bank.bankrupt();   //은행 파산임
            } else //Can be solved with equity (거의 최후 수단)
                j.put("Message", "Reserve was lacking, but bankrun is covered with equity.");
        }

        bank.total_money = bank.reserve + bank.loans + bank.deposit + bank.equity;
        return j;
    }
}