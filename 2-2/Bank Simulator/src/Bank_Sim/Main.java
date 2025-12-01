/*
Sunghyun Park (2025) All Rights Reserved.
BANK SIMULATOR (2025)
This program is a simulation of Fractional-Reserve Banking, mostly focused on the United States.
 */
package Bank_Sim;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import org.json.simple.JSONObject;

public class Main extends JFrame { //GUI

    private int time = 0; //sim time (tick)
    private Banks banks = new Banks();
    private Households households = new Households();
    private Fed fed = new Fed();
    private BankUtils bankUtils = new BankUtils();
    private FedUtils fedUtils = new FedUtils();

    //components
    private JLabel timeLabel;
    private JTextArea logArea;
    private JTextArea stateArea;  //Overall bank

    //Options related to bank
    private JComboBox<String> bankModeBox;
    private JTextField bankReserveField;
    private JTextField bankDepositField;
    private JTextField bankEquityField;
    private JTextField bankTotalField;
    private JTextField bankRRatioField;
    private JTextField rrField; // reserve ratio
    private JTextField drField; // discount rate
    //new bank/hh
    private JTextField bankNameField;
    private JTextField hhNameField;
    //어느거 볼지 선택
    private JComboBox<String> bankSelectBox;  // Bank Actions에서 볼 은행
    private JComboBox<String> hhSelectBox;    // Household 선택
    private JComboBox<String> hbBankBox;      // Household-Bank 거래에서 선택할 은행
    private JComboBox<String> lenderBox;      // Interbank: 빌려주는 은행
    private JComboBox<String> borrowerBox;    // Interbank: 빌리는 은행
    private JTextField runRatioField; //bankrun
    //exchange amount
    private JTextField hbAmountField;
    private JTextField bbAmountField;
    private Timer timer;

    public Main() {
        super("Bank Simulator");

        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1100, 650);
        setLocationRelativeTo(null);

        buildUI();
        timer();
    }

    //timer (how much time between each tick
    private void timer() {
        timer = new Timer(7000, new ActionListener() { //7000 -> 7sec (for each tick)
            public void actionPerformed(ActionEvent e) {
                stepSimulation();
            }
        });
    }
    private void stepSimulation() { //for each tick
        time++;
        timeLabel.setText("Time : " + time);
        //get all interest rate updated
        for (int i = 0; i < banks.banks.size(); i++) {
            Bank b = banks.banks.get(i);
            bankUtils.applyInterest(b, b.loanRate, b.depositRate);
            JSONObject req = bankUtils.checkReserveReq(b, fed.rRatio);
            Object ok = req.get("Req");
            if (ok instanceof Boolean && !((Boolean) ok)) {
                logArea.append("[t=" + time + "] " + b.name + " does not meet reserve requirement.\n");
            }
        }
        updateStateView();
    }
    //GUI
    private void buildUI() {
        setLayout(new BorderLayout());
        //time (on the up end)
        timeLabel = new JLabel("Time : 0");
        timeLabel.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));
        add(timeLabel, BorderLayout.NORTH);

        //logs
        logArea = new JTextArea();
        logArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(logArea);
        add(scrollPane, BorderLayout.CENTER);

        // bank & households states
        stateArea = new JTextArea();
        stateArea.setEditable(false);
        JScrollPane stateScroll = new JScrollPane(stateArea);
        stateScroll.setPreferredSize(new Dimension(280, 0));
        add(stateScroll, BorderLayout.WEST);

        //control panel (right end)
        JPanel rightPanel = new JPanel();
        rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS));

        JScrollPane controlScroll = new JScrollPane(rightPanel);
        controlScroll.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        controlScroll.setPreferredSize(new Dimension(600, 0)); //RIght panel (자꾸 잘려서 확 넓힘)
        add(controlScroll, BorderLayout.EAST);

        //sim controls
        JPanel simPanel = new JPanel();
        simPanel.setBorder(BorderFactory.createTitledBorder("Simulation"));
        JButton startBtn = new JButton("Start");
        JButton stopBtn = new JButton("Stop");
        JButton stepBtn = new JButton("Step");

        //listeners
        startBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                timer.start();
                logArea.append("Simulation started.\n");
            }
        });

        stopBtn.addActionListener(new ActionListener() { //''
            public void actionPerformed(ActionEvent e) {
                timer.stop();
                logArea.append("Simulation stopped.\n");
            }
        });

        stepBtn.addActionListener(new ActionListener() { //''
            public void actionPerformed(ActionEvent e) {
                stepSimulation();
                logArea.append("One step executed.\n");
            }
        });

        //start & end
        simPanel.add(startBtn);
        simPanel.add(stopBtn);
        simPanel.add(stepBtn);
        rightPanel.add(simPanel);

        //FED settings (헷갈려서 따로뺴둠)
        JPanel fedPanel = new JPanel(new GridLayout(3, 2, 3, 3));
        fedPanel.setBorder(BorderFactory.createTitledBorder("Fed"));
        fedPanel.add(new JLabel("Reserve Ratio"));
        rrField = new JTextField(String.valueOf(fed.rRatio));
        fedPanel.add(rrField);
        fedPanel.add(new JLabel("Discount Rate"));
        drField = new JTextField(String.valueOf(fed.dRate));
        fedPanel.add(drField);
        JButton applyFedBtn = new JButton("Apply");
        fedPanel.add(applyFedBtn);

        //FED listeners
        applyFedBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                try {
                    float newRR = Float.parseFloat(rrField.getText());
                    float newDR = Float.parseFloat(drField.getText());

                    JSONObject res1 = fed.changeRR(newRR);
                    appendJson("changeRR", res1);

                    JSONObject res2 = fed.changeDR(newDR);
                    appendJson("changeDR", res2);
                } catch (NumberFormatException ex) {
                    logArea.append("Fed parameters must be numbers.\n");
                }
            }
        });

        rightPanel.add(fedPanel);

        //new bank. & households
        JPanel createPanel = new JPanel();
        createPanel.setLayout(new GridLayout(10, 2, 3, 3));
        createPanel.setBorder(BorderFactory.createTitledBorder("Create Agents"));

        // Bank mode (constructor)
        createPanel.add(new JLabel("Bank Mode"));
        bankModeBox = new JComboBox<>(new String[]{
                "Default (name only)",
                "Reserve / Deposit / Equity",
                "TotalMoney + rRatio + Equity"
        });
        createPanel.add(bankModeBox);

        createPanel.add(new JLabel("Bank Name"));
        bankNameField = new JTextField();
        createPanel.add(bankNameField);

        //Bank params
        createPanel.add(new JLabel("Reserve"));
        bankReserveField = new JTextField();
        createPanel.add(bankReserveField);

        createPanel.add(new JLabel("Deposit"));
        bankDepositField = new JTextField();
        createPanel.add(bankDepositField);

        createPanel.add(new JLabel("Equity"));
        bankEquityField = new JTextField();
        createPanel.add(bankEquityField);

        createPanel.add(new JLabel("Total Money"));
        bankTotalField = new JTextField();
        createPanel.add(bankTotalField);

        createPanel.add(new JLabel("rRatio (for total)"));
        bankRRatioField = new JTextField();
        createPanel.add(bankRRatioField);

        JButton newBankBtn = new JButton("New Bank");
        createPanel.add(newBankBtn);
        createPanel.add(new JLabel()); // 빈 칸

        // Household 생성
        createPanel.add(new JLabel("Household Name"));
        hhNameField = new JTextField();
        createPanel.add(hhNameField);

        JButton newHHBtn = new JButton("New Household");
        createPanel.add(newHHBtn);
        createPanel.add(new JLabel());

        //actually create new bank
        newBankBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                String name = bankNameField.getText().trim();
                if (name.length() == 0) {
                    name = "Bank" + (banks.banks.size() + 1);
                }
                Bank b;
                int mode = bankModeBox.getSelectedIndex();
                try {
                    if (mode == 0) {
                        //default contructor
                        b = new Bank(name);
                    } else if (mode == 1) {
                        //reserve *& deposit & equity
                        float r = Float.parseFloat(bankReserveField.getText());
                        float d = Float.parseFloat(bankDepositField.getText());
                        float eVal = Float.parseFloat(bankEquityField.getText());
                        b = new Bank(name, r, d, eVal);
                    } else {
                        //total_money & rRatio & equity
                        float total = Float.parseFloat(bankTotalField.getText());
                        float rr = Float.parseFloat(bankRRatioField.getText());
                        float eVal = Float.parseFloat(bankEquityField.getText());
                        b = new Bank(name, total, rr, eVal, "gui");
                    }
                } catch (NumberFormatException ex) {
                    logArea.append("Bank parameters must be valid numbers.\n");
                    return;
                }

                // Bank doesn't init name, so this line is mandatory
                b.name = name;

                JSONObject res = banks.newBank(b);
                appendJson("newBank", res);
                if (Boolean.TRUE.equals(res.get("Success"))) {
                    String label = "[" + b.id + "] " + b.name;
                    bankSelectBox.addItem(label);
                    if (hbBankBox != null)    hbBankBox.addItem(label);
                    if (lenderBox != null)    lenderBox.addItem(label);
                    if (borrowerBox != null)  borrowerBox.addItem(label);
                    updateStateView();
                }
            }
        });

        //new households
        newHHBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                String name = hhNameField.getText().trim();
                if (name.length() == 0) {
                    name = "HH" + (households.households.size() + 1);
                }
                Household h = new Household(name);
                JSONObject res = households.newBank(h);
                appendJson("newHousehold", res);
                if (hhSelectBox != null) {
                    hhSelectBox.addItem("[" + h.id + "] " + h.name);
                }
                updateStateView();
            }
        });

        rightPanel.add(createPanel);

        //bank selct &
        JPanel bankPanel = new JPanel();
        bankPanel.setLayout(new GridLayout(5, 1, 3, 3));
        bankPanel.setBorder(BorderFactory.createTitledBorder("Bank Actions"));

        bankSelectBox = new JComboBox<String>();
        bankPanel.add(bankSelectBox);

        JButton viewBankBtn = new JButton("View Bank");
        bankPanel.add(viewBankBtn);

        JButton checkRRBtn = new JButton("Check Reserve");
        bankPanel.add(checkRRBtn);

        JPanel runPanel = new JPanel(new BorderLayout(3, 3));
        runPanel.add(new JLabel("Run Ratio"), BorderLayout.WEST);
        runRatioField = new JTextField("0.2");
        runPanel.add(runRatioField, BorderLayout.CENTER);
        bankPanel.add(runPanel);

        JButton runBtn = new JButton("Bank Run");
        bankPanel.add(runBtn);

        //see selected banks
        viewBankBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank b = getSelectedBank();
                if (b == null) {
                    logArea.append("No bank selected.\n");
                    return;
                }
                logArea.append("Bank [" + b.id + "] " + b.name + "\n");
                logArea.append("reserve : " + fmtB(b.reserve) + "\n");
                logArea.append("loans   : " + fmtB(b.loans) + "\n");
                logArea.append("deposit : " + fmtB(b.deposit) + "\n");
                logArea.append("equity  : " + fmtB(b.equity) + "\n");
                logArea.append("total   : " + fmtB(b.total_money) + "\n");
            }
        });

        //Check reserve requirement of selected bank
        checkRRBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank b = getSelectedBank();
                if (b == null) {
                    logArea.append("No bank selected.\n");
                    return;
                }
                JSONObject res = bankUtils.checkReserveReq(b, fed.rRatio);
                appendJson("checkReserveReq (Bank " + b.id + ")", res);
            }
        });

        //BANKRUN!!!!!!!!
        runBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank b = getSelectedBank();
                if (b == null) {
                    logArea.append("No bank selected.\n");
                    return;
                }
                try {
                    float r = Float.parseFloat(runRatioField.getText());
                    JSONObject res = bankUtils.handleBankRun(b, r);
                    appendJson("handleBankRun (Bank " + b.id + ")", res);
                    updateStateView();
                } catch (NumberFormatException ex) {
                    logArea.append("Run ratio must be a number.\n");
                }
            }
        });

        rightPanel.add(bankPanel);

        //Household & bank panel
        JPanel hbPanel = new JPanel();
        hbPanel.setLayout(new GridLayout(7, 1, 3, 3));
        hbPanel.setBorder(BorderFactory.createTitledBorder("Household - Bank"));

        //Which household to use
        hhSelectBox = new JComboBox<String>();
        hbPanel.add(hhSelectBox);

        //select banks for household to interact
        hbBankBox = new JComboBox<String>();
        hbPanel.add(hbBankBox);

        JPanel hbAmountPanel = new JPanel(new BorderLayout(3, 3));
        hbAmountPanel.add(new JLabel("Amount"), BorderLayout.WEST);
        hbAmountField = new JTextField("1000");
        hbAmountPanel.add(hbAmountField, BorderLayout.CENTER);
        hbPanel.add(hbAmountPanel);
        JButton depositBtn = new JButton("Deposit");
        JButton loanBtn   = new JButton("Give Loan");
        JButton repayBtn  = new JButton("Repay Loan");
        JButton viewHHBtn = new JButton("View Relations");
        hbPanel.add(depositBtn);
        hbPanel.add(loanBtn);
        hbPanel.add(repayBtn);
        hbPanel.add(viewHHBtn);
        //HouseholdtoBank (Deposit, 예금)
        depositBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank b = getBankFromBox(hbBankBox);
                Household h = getSelectedHousehold();
                if (b == null || h == null) {
                    logArea.append("Select both a bank and a household.\n");
                    return;
                }
                float amount;
                try {
                    amount = Float.parseFloat(hbAmountField.getText());
                } catch (NumberFormatException ex) {
                    logArea.append("Amount must be a number.\n");
                    return;
                }
                bankUtils.deposit(amount, h, b);
                updateStateView();
            }
        });

        //Back to household (first loan)
        loanBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank b = getBankFromBox(hbBankBox);
                Household h = getSelectedHousehold();
                if (b == null || h == null) {
                    logArea.append("Select both a bank and a household.\n");
                    return;
                }
                float amount;
                try {
                    amount = Float.parseFloat(hbAmountField.getText());
                } catch (NumberFormatException ex) {
                    logArea.append("Amount must be a number.\n");
                    return;
                }
                bankUtils.giveLoan(amount, h, b);
                updateStateView();
            }
        });

        //repaying loan
        repayBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank b = getBankFromBox(hbBankBox);
                Household h = getSelectedHousehold();
                if (b == null || h == null) {
                    logArea.append("Select both a bank and a household.\n");
                    return;
                }
                float amount;
                try {
                    amount = Float.parseFloat(hbAmountField.getText());
                } catch (NumberFormatException ex) {
                    logArea.append("Amount must be a number.\n");
                    return;
                }
                JSONObject res = bankUtils.repayLoan(amount, h, b);
                appendJson("repayLoan", res);
                updateStateView();
            }
        });

        //check selected household's relations
        viewHHBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Household h = getSelectedHousehold();
                if (h == null) {
                    logArea.append("No household selected.\n");
                    return;
                }
                logArea.append("Household [" + h.id + "] " + h.name + "\n");
                logArea.append("  Total Money: " + fmtB(h.total_money) + "\n");
                if (h.relations == null || h.relations.isEmpty()) {
                    logArea.append("  (no relations)\n");
                } else {
                    for (int i = 0; i < h.relations.size(); i++) {
                        float[] rel = h.relations.get(i);
                        int bankId = (int) rel[0];
                        float borrowed = rel[1];
                        float deposited = rel[2];
                        String bankName = "";
                        for (Bank b : banks.banks) {
                            if (b.id == bankId) {
                                bankName = b.name;
                                break;
                            }
                        }
                        logArea.append("  -> Bank [" + bankId + "] " + bankName
                                + " | Borrowed: " + fmtB(borrowed)
                                + " | Deposited: " + fmtB(deposited) + "\n");
                    }
                }
                logArea.append("\n");
            }
        });

        rightPanel.add(hbPanel);

        //Interact actions panel
        JPanel ibPanel = new JPanel();
        ibPanel.setLayout(new GridLayout(6, 1, 3, 3));
        ibPanel.setBorder(BorderFactory.createTitledBorder("Interbank"));
        lenderBox = new JComboBox<String>();
        borrowerBox = new JComboBox<String>();
        JPanel lenderPanel = new JPanel(new BorderLayout(3, 3));
        lenderPanel.add(new JLabel("Lender"), BorderLayout.WEST);
        lenderPanel.add(lenderBox, BorderLayout.CENTER);
        ibPanel.add(lenderPanel);

        JPanel borrowerPanel = new JPanel(new BorderLayout(3, 3));
        borrowerPanel.add(new JLabel("Borrower"), BorderLayout.WEST);
        borrowerPanel.add(borrowerBox, BorderLayout.CENTER);
        ibPanel.add(borrowerPanel);
        JPanel bbAmountPanel = new JPanel(new BorderLayout(3, 3));
        bbAmountPanel.add(new JLabel("Amount"), BorderLayout.WEST);
        bbAmountField = new JTextField("1000"); //? 흠..
        bbAmountPanel.add(bbAmountField, BorderLayout.CENTER);
        ibPanel.add(bbAmountPanel);
        JButton borrowBtn    = new JButton("Borrow From");
        JButton repayBankBtn = new JButton("Repay To");
        ibPanel.add(borrowBtn);
        ibPanel.add(repayBankBtn);
        //borrowing (정확히는 차입)
        borrowBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank lender   = getBankFromBox(lenderBox);
                Bank borrower = getBankFromBox(borrowerBox);
                if (lender == null || borrower == null) {
                    logArea.append("Select both lender and borrower banks.\n");
                    return;
                }
                float amount;
                try {
                    amount = Float.parseFloat(bbAmountField.getText());
                } catch (NumberFormatException ex) {
                    logArea.append("Amount must be a number.\n");
                    return;
                }
                JSONObject res = bankUtils.borrowFromBank(amount, lender, borrower);
                appendJson("borrowFromBank", res);
                updateStateView();
            }
        });

        //Repay to (상환)
        repayBankBtn.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                Bank lender   = getBankFromBox(lenderBox);
                Bank borrower = getBankFromBox(borrowerBox);
                if (lender == null || borrower == null) {
                    logArea.append("Select both lender and borrower banks.\n");
                    return;
                }
                float amount;
                try {
                    amount = Float.parseFloat(bbAmountField.getText());
                } catch (NumberFormatException ex) {
                    logArea.append("Amount must be a number.\n");
                    return;
                }
                JSONObject res = bankUtils.repayToBank(amount, lender, borrower);
                appendJson("repayToBank", res);
                updateStateView();
            }
        });
        rightPanel.add(ibPanel);

        updateStateView();
    }

    //too large dollars 보기 좋게 했음
    private String fmtB(float v) {
        return String.format("%,.1fB", v / 1_000_000_000f);
    }

    private Bank getSelectedBank() {
        int idx = bankSelectBox.getSelectedIndex();
        if (idx < 0 || idx >= banks.banks.size()) {
            return null;
        }
        return banks.banks.get(idx);
    }

    //combobox hh check
    private Household getSelectedHousehold() {
        if (hhSelectBox == null) return null;
        int idx = hhSelectBox.getSelectedIndex();
        if (idx < 0 || idx >= households.households.size()) {
            return null;
        }
        return households.households.get(idx);
    }

    // '' get bank
    private Bank getBankFromBox(JComboBox<String> box) {
        if (box == null) return null;
        int idx = box.getSelectedIndex();
        if (idx < 0 || idx >= banks.banks.size()) {
            return null;
        }
        return banks.banks.get(idx);
    }

    private void appendJson(String title, JSONObject obj) {
        if (obj == null) return;
        Object msg = obj.get("Message");
        logArea.append("[" + title + "] " + msg + "\n");
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                Main m = new Main();
                m.setVisible(true);
            }
        });
    }

    //bank & household status to combobox
    private void updateStateView() {
        if (stateArea == null) return;
        StringBuilder sb = new StringBuilder();

        sb.append("=== Banks ===\n");
        for (Bank b : banks.banks) {
            sb.append("[").append(b.id).append("] ").append(b.name).append("\n");
            sb.append("  R: ").append(fmtB(b.reserve))
              .append(" | L: ").append(fmtB(b.loans))
              .append(" | D: ").append(fmtB(b.deposit))
              .append("\n");
            sb.append("  E: ").append(fmtB(b.equity))
              .append(" | T: ").append(fmtB(b.total_money))
              .append("\n\n");
        }

        sb.append("=== Households ===\n");
        for (Household h : households.households) {
            sb.append("[").append(h.id).append("] ").append(h.name).append("\n");
            sb.append("  Money: ").append(h.total_money).append("\n\n");
        }

        stateArea.setText(sb.toString());
    }
}

//새벽5시완성.....