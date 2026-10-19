function m2_plots(c,r,sensitivity,comparison,out)
f=figure('Visible','off','Color','w','Position',[50 50 1200 760]);tiledlayout(2,2);
for k=1:4
    nexttile;plot(r{k}.t,r{k}.T_K-273.15,'LineWidth',1.1);xlabel('Time (s)');ylabel('Lumped temperature (C)');
    title({r{k}.id,'S3 CONCEPT PREDICTION - NOT CALIBRATED'},'Interpreter','none');grid on;
    if k==4,legend(strrep(c.ids,'_',' '),'Location','eastoutside','FontSize',7);end
end
exportgraphics(f,fullfile(out,'node_temperatures.png'),'Resolution',200);exportgraphics(f,fullfile(out,'node_temperatures.svg'),'ContentType','vector');close(f);
f=figure('Visible','off','Color','w','Position',[50 50 1200 680]);tiledlayout(2,2);
for k=1:4
    node=[1 7 10 8];j=node(k);nexttile;hold on;
    for a=1:3,plot(r{a}.t,r{a}.T_K(:,j)-273.15,'LineWidth',1.4);end
    title({strrep(c.ids{j},'_',' '),'S3 controlled source-mask comparison'});xlabel('Time (s)');ylabel('Temperature (C)');legend('A internal','B brake','C combined');grid on;
end
exportgraphics(f,fullfile(out,'source_comparison.png'),'Resolution',200);exportgraphics(f,fullfile(out,'source_comparison.svg'),'ContentType','vector');close(f);
f=figure('Visible','off','Color','w','Position',[50 50 1200 680]);tiledlayout(2,2);
for a=1:2
    k=a+2;nexttile;plot(r{k}.t,r{k}.path_W,'LineWidth',1.2);xlabel('Time (s)');ylabel('Signed heat INTO drive (W)');
    title({r{k}.id,'S3 unique domain-cut heat flows'},'Interpreter','none');legend('Radiation','Hot air','Solid incl. mount');grid on;
    nexttile;hold on;
    plot(r{k}.t,r{k}.path_net_J/1000,'LineWidth',1.4);plot(r{k}.t,r{k}.path_forward_J/1000,'--','LineWidth',1);
    xlabel('Time (s)');ylabel('Cumulative heat (kJ)');title('S3 solid = net; dashed = forward-positive');grid on;
    legend('Radiation net','Hot-air net','Solid net','Radiation forward','Hot-air forward','Solid forward','Location','best','FontSize',7);
end
exportgraphics(f,fullfile(out,'path_heat_flows.png'),'Resolution',200);exportgraphics(f,fullfile(out,'path_heat_flows.svg'),'ContentType','vector');close(f);
f=figure('Visible','off','Color','w','Position',[50 50 1200 500]);tiledlayout(1,2);
nexttile;bar(comparison.max_C_minus_A_K);xticks(1:c.N);xticklabels(strrep(c.ids,'_',' '));xtickangle(40);
ylabel('Max instantaneous T_C - T_A (K)');title('S3 additional brake-source influence');grid on;
nexttile;nom=r{3}.summary.peak_winding_C;bar(sensitivity.peak_winding_C-nom);xticks(1:height(sensitivity));
xticklabels(strrep(cellstr(sensitivity.case_id),'_',' '));xtickangle(65);ylabel('Peak winding change from C (K)');title('S3 parameter/loss uncertainty - NOT confidence');grid on;
exportgraphics(f,fullfile(out,'coupling_sensitivity.png'),'Resolution',200);exportgraphics(f,fullfile(out,'coupling_sensitivity.svg'),'ContentType','vector');close(f);
f=figure('Visible','off','Color','w','Position',[50 50 1150 430]);tiledlayout(1,2);
nexttile;plot(r{3}.t,r{3}.T_K(:,[6 7])-r{1}.T_K(:,[6 7]),'LineWidth',1.5);
xlabel('Time (s)');ylabel('Additional temperature (K)');legend('Gear oil','Gear case');title('S3 brake-source influence: C - A');grid on;
nexttile;plot(r{3}.t,r{3}.T_K(:,[8 9 10 11])-r{1}.T_K(:,[8 9 10 11]),'LineWidth',1.5);
xlabel('Time (s)');ylabel('Additional temperature (K)');legend('Motor case','Stator','Winding','Rotor/other');title('S3 delayed coupling: C - A');grid on;
exportgraphics(f,fullfile(out,'additional_brake_influence.png'),'Resolution',200);exportgraphics(f,fullfile(out,'additional_brake_influence.svg'),'ContentType','vector');close(f);
end
