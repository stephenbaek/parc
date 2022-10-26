import numpy as np
from math import sqrt
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

def visualize_inference(
    data_in: np.ndarray,
    data_out: np.ndarray,
    time_idx: list = None,
    fields: list = None,
):
    """plot the inference results

    Args:
        data_in (np.ndarray):   ground truth label
        data_out (np.ndarray):  model prediction
        time_idx (list[int]):   list of the time index to plot
        fields (list[bool]):    list of selecting which fields to plot. If None, plot all fields
    """
    # todo: missing


def plot_rmse(all_rmse, t_idx):
    """Root mean squared error plot, plotted as boxplot
    Args:
        all_rmse : total root mean squared output from data
        t_idx (list[int]): list of the time index to plot
    """
    sample_name = "RMSE"
    plt.figure(figsize=[17, 4])
    plt.boxplot(
        all_rmse,
        whis=[5, 95],
        medianprops=dict(linewidth=0),
        meanline=True,
        showmeans=True,
        showfliers=False,
        labels=None,
        positions=t_idx,
    )
    for i in range(len(all_rmse)):
        plt.scatter(t_idx, all_rmse[i, :], alpha=0.4, color="b")
        
    # Add labels and title
    plt.title(sample_name)
    plt.xlabel("ns")
    plt.ylabel("RMSE")
    plt.legend()
    plt.show()


def plot_r2(all_r2, t_idx):
    """R2 score plot using r2 scores calculated in losses module, plotted as a boxplot
    Args:
        all_r2 : R2 score 
        t_idx (list[int]): list of the time index to plot
    """

    sample_name = "R2"
    plt.figure(figsize=[17, 4])

    plt.boxplot(
        all_r2,
        whis=[5, 95],
        medianprops=dict(linewidth=0),
        meanline=True,
        showmeans=True,
        showfliers=False,
        positions=t_idx,
    )
    for i in range(len(all_r2)):
        plt.scatter(t_idx, all_r2[i, :], alpha=0.4, color="b")

    # Add labels and title
    plt.title(sample_name)
    plt.xlabel("ns")
    plt.ylabel("R2")
    plt.axis([0.5, 15.5, 0, 1])
    plt.legend()
    plt.show()


def plot_sensitivity_area(y_true, y_pred, t_idx):
    """plot of the average hotspot area rate of change used to show predicted growth
    Args:
        y_true (np.ndarray): true values for temp/press found in input dataset
        y_pred (np.ndarray): model predicted values for temp/press
        t_idx (list[int]): list of the time index to plot
    """
    (
        area_mean,
        area_error1,
        area_error2,
        gt_area_mean,
        gt_area_error1,
        gt_area_error2,
    ) = Calculate_avg_sensitivity(y_pred[:, :, :, 1:], y_true[:, :, :, 1:])

    plt.figure(figsize=(6, 4))

    plt.plot(t_idx, gt_area_mean, "b-", label="Ground truth")
    plt.plot(t_idx, area_mean, "r-", label="Prediction")

    plt.fill_between(t_idx, gt_area_error1, gt_area_error2, color="blue", alpha=0.2)
    plt.fill_between(t_idx, area_error1, area_error2, color="red", alpha=0.2)

    # Add labels and title
    plt.title(r"Ave. Hotspot Area Rate of Change ($\dot{A_{hs}}$)", fontsize=14, pad=15)
    # x-axis: time in nanoseconds
    plt.xlabel(r"t ($ns$)", fontsize=12)
    # y-axis: area/time
    plt.ylabel(r"$\dot{A_{hs}}$ ($\mu m^2$/$ns$)", fontsize=12)
    plt.legend(loc=2, fontsize=11)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.savefig("area_growth_plot.png")
    plt.show()

def plot_sensitivity_temperature(y_true, y_pred, t_idx):
    """plot of the average hotspot temperature rate of change used to show predicted growth
    Args:
        y_true (np.ndarray): true values for temp found in input dataset
        y_pred (np.ndarray): model predicted values for temp
        t_idx (list[int]): list of the time index to plot
    """  
    (
        temp_mean,
        temp_error1,
        temp_error2,
        gt_temp_mean,
        gt_temp_error1,
        gt_temp_error2,
    ) = Calculate_avg_sensitivity(y_pred[:, :, :, 1:], y_true[:, :, :, 1:])

    plt.figure(figsize=(6, 4))

    plt.plot(t_idx, gt_temp_mean, "b-", label="Ground truth")
    plt.plot(t_idx, temp_mean, "r-", label="Prediction")

    plt.fill_between(t_idx, gt_temp_error1, gt_temp_error2, color="blue", alpha=0.2)
    plt.fill_between(t_idx, temp_error1, temp_error2, color="red", alpha=0.2)

    # Add labels and title
    plt.title(
        r"Ave. Hotspot Temperature Rate of Change ($\dot{T_{hs}}$)", fontsize=14, pad=15
    )
    # x-axis: time in nanoseconds
    plt.xlabel(r"t ($ns$)", fontsize=12)
    # y-axis: temperature/time
    plt.ylabel(r"$\dot{T_{hs}}$ ($K$/$ns$)", fontsize=12)
    plt.legend(fontsize=11)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.savefig("temp_growth_plot.png")
    plt.show()

def plot_saliency(y_pred):
    """plot of the saliency of the predicted values, shows where the growth originates in prediction
    Args:
        y_pred (np.ndarray): model predicted values for temp
    """  
    norm_T_max = 4000
    norm_T_min = 300
    threshold = 875  # 875 Temperature(K), max hotspot temperature threshold

    pred_data = np.squeeze(y_pred[0][1, :, :, 22])
    pred_data = (pred_data + 1.0) / 2.0
    pred_data = (pred_data * (norm_T_max - norm_T_min)) + norm_T_min
    pred_mask = pred_data > threshold

    plt.imshow(np.squeeze(pred_mask), cmap="RdGy_r", vmin=-0.0, vmax=1.0)
    ax = plt.gca()
    ax.set_xticks([])
    ax.set_yticks([])
