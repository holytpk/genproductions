import uproot
import awkward as ak
import vector
import numpy as np
import hist
import matplotlib.pyplot as plt
import mplhep
import pickle
import glob
from uncertainties import unumpy as unp
from tqdm import tqdm, trange
import os

def save_histograms(h_ref_dict, h_eft_dict, outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "histograms.pkl"), "wb") as f:
        pickle.dump({"ref": h_ref_dict, "eft": h_eft_dict}, f)

# check the return statement for what come out of this function 
def compute_gen_spin_corrs(E, px, py, pz, is_top, is_antitop, event_mask,
                           top_with_wplus_daughter_mask, antitop_with_wminus_daughter_mask,
                           mother_is_Wplus, mother_is_Wminus,
                           Wplus_daughter_mask, Wminus_daughter_mask,
                           mother_is_top, mother_is_antitop,
                           is_bottom_from_top, is_antibottom_from_antitop):

    def cos_angle(x):
        return ak.to_numpy(ak.fill_none(np.cos(x), 0.0))

    def select_unique(vec, *masks):
        mask = masks[0]
        for m in masks[1:]:
            mask = mask & m
        vec_masked = vec[mask]
        return ak.firsts(vec_masked, axis=1)

    #print("Applying masks and building four-vectors...")

    genvec = vector.Array(ak.zip({"E": E, "px": px, "py": py, "pz": pz}))

    tops = select_unique(genvec, is_top, top_with_wplus_daughter_mask, event_mask)
    tbars = select_unique(genvec, is_antitop, antitop_with_wminus_daughter_mask, event_mask)
    ls = select_unique(genvec, mother_is_Wminus, Wminus_daughter_mask, event_mask)
    lbars = select_unique(genvec, mother_is_Wplus, Wplus_daughter_mask, event_mask)
    bs = select_unique(genvec, mother_is_top, is_bottom_from_top, event_mask)
    bbars = select_unique(genvec, mother_is_antitop, is_antibottom_from_antitop, event_mask)

    #print("Constructing vectors...")
    #print("Boosting to ttbar rest frame...")

    ttbar_frame = tops + tbars
    boosted_tops = tops.boostCM_of(ttbar_frame)
    boosted_tbars = tbars.boostCM_of(ttbar_frame)
    boosted_ls = ls.boostCM_of(ttbar_frame).boostCM_of(boosted_tbars)
    boosted_lbars = lbars.boostCM_of(ttbar_frame).boostCM_of(boosted_tops)

    #print("Calculating angles and constructing observables...")

    p_axis = vector.obj(x=0, y=0, z=1)
    k_axis = boosted_tops.to_xyz().unit()
    scattering_angle = k_axis.theta
    sin_scat_angle = np.sin(scattering_angle)
    sin_scat_angle = np.where(np.abs(sin_scat_angle) < 1e-5, 1e-5, sin_scat_angle)
    axis_coeff = np.sign(np.cos(scattering_angle)) / np.abs(sin_scat_angle)
    r_axis = axis_coeff * (p_axis - (k_axis * np.cos(scattering_angle)))
    n_axis = axis_coeff * p_axis.cross(k_axis)

    ll_cHel = cos_angle(boosted_lbars.deltaangle(boosted_ls))
    cos_theta1k = cos_angle(boosted_lbars.deltaangle(k_axis))
    cos_theta1r = cos_angle(boosted_lbars.deltaangle(r_axis))
    cos_theta1n = cos_angle(boosted_lbars.deltaangle(n_axis))
    cos_theta2k = cos_angle(boosted_ls.deltaangle(-1 * k_axis))
    cos_theta2r = cos_angle(boosted_ls.deltaangle(-1 * r_axis))
    cos_theta2n = cos_angle(boosted_ls.deltaangle(-1 * n_axis))

    ttbar_mass = ak.to_numpy(ak.fill_none((tops + tbars).M, 0.0))
    scattering_angle = ak.to_numpy(ak.fill_none(scattering_angle, 0.0))

    valid_mask = (
        ~np.isnan(ll_cHel) & ~np.isnan(cos_theta1k) & ~np.isnan(cos_theta1r) & ~np.isnan(cos_theta1n) &
        ~np.isnan(cos_theta2k) & ~np.isnan(cos_theta2r) & ~np.isnan(cos_theta2n) &
        ~np.isnan(ttbar_mass) & ~np.isnan(scattering_angle) &
        (ttbar_mass > 0)
    )

    ls = ls[valid_mask]
    lbars = lbars[valid_mask]
    bs = bs[valid_mask]
    bbars = bbars[valid_mask]
    tops = tops[valid_mask]
    tbars = tbars[valid_mask]    

    ll_cHel = ll_cHel[valid_mask]
    cos_theta1k = cos_theta1k[valid_mask]
    cos_theta1r = cos_theta1r[valid_mask]
    cos_theta1n = cos_theta1n[valid_mask]
    cos_theta2k = cos_theta2k[valid_mask]
    cos_theta2r = cos_theta2r[valid_mask]
    cos_theta2n = cos_theta2n[valid_mask]
    ttbar_mass = ttbar_mass[valid_mask]
    scattering_angle = scattering_angle[valid_mask]

    B1 = np.stack([cos_theta1k, cos_theta1r, cos_theta1n], axis=1)
    B2 = np.stack([cos_theta2k, cos_theta2r, cos_theta2n], axis=1)
    C = np.stack([
        np.stack([cos_theta1k * cos_theta2k, cos_theta1k * cos_theta2r, cos_theta1k * cos_theta2n], axis=-1),
        np.stack([cos_theta1r * cos_theta2k, cos_theta1r * cos_theta2r, cos_theta1r * cos_theta2n], axis=-1),
        np.stack([cos_theta1n * cos_theta2k, cos_theta1n * cos_theta2r, cos_theta1n * cos_theta2n], axis=-1)
    ], axis=1).transpose(2, 0, 1)

    #print("Finished computing spin correlations.")

    return scattering_angle, ttbar_mass, B1, B2, C, ll_cHel, ls, lbars, bs, bbars, tops, tbars, valid_mask

def compute_composite_C(C):
    c_kk, c_rr, c_nn = C[0, :, 0], C[1, :, 1], C[2, :, 2]
    c_nk, c_kn = C[2, :, 0], C[0, :, 2]
    c_rk, c_kr = C[1, :, 0], C[0, :, 1]
    c_nr, c_rn = C[2, :, 1], C[1, :, 2]
    c_kj, c_rq = C[0, :, 1], C[1, :, 2]  # approximate for kj and rq

    composites = {
        "c_kn": c_kn,
        "c_rk": c_rk,
        "c_rn": c_rn,
        "c_kk": c_kk,
        "c_rr": c_rr,
        "c_nn": c_nn,
        "c_kr": c_kr,
        "c_rk": c_rk,
        "c_kn": c_kn,
        "c_nk": c_nk,
        "c_rn": c_rn,
        "c_nr": c_nr,
        "c_Pnk": c_nk + c_kn,
        "c_Mnk": c_nk - c_kn,
        "c_Prk": c_rk + c_kr,
        "c_Mrk": c_rk - c_kr,
        "c_Pnr": c_nr + c_kn,
        "c_Mnr": c_nr - c_kn,
        "c_han": c_kk - c_rr - c_nn,
        "c_sca": -c_kk + c_rr - c_nn,
        "c_tra": -c_kk - c_rr + c_nn,
        "c_kjL": -c_kj - c_rr - c_nn,
        "c_rqL": -c_kk - c_rq - c_nn,
        "c_rkP": -c_rk - c_kr - c_nn,
        "c_rkM": -c_rk + c_kr - c_nn,
        "c_nrP": -c_nr - c_rn - c_kk,
        "c_nrM": -c_nr + c_rn - c_kk,
        "c_nkP": -c_nk - c_kn - c_rr,
        "c_nkM": -c_nk + c_kn - c_rr,
    }

    return composites


def get_valid_root_files_with_tree(filelist, tree_name="Events"):
    valid_files = []
    for f in filelist:
        try:
            with uproot.open(f) as file:
                if tree_name in file:
                    # Optional: make sure "Events" tree is readable
                    _ = file[tree_name].num_entries
                    valid_files.append(f)
        except Exception:
            continue
    return valid_files

# Function to extract necessary arrays and masks from dataset
def extract_inputs(arrays):
    pt = arrays["GenPart_pt"]
    eta = arrays["GenPart_eta"]
    phi = arrays["GenPart_phi"]
    mass = arrays["GenPart_mass"]
    pdgId = arrays["GenPart_pdgId"]
    mother_idx = arrays["GenPart_genPartIdxMother"]

    genvec = vector.Array(ak.zip({"pt": pt, "eta": eta, "phi": phi, "mass": mass}))

    is_top = pdgId == 6
    is_antitop = pdgId == -6
    is_bottom = pdgId == 5
    is_antibottom = pdgId == -5
    is_electron = abs(pdgId) == 11
    is_muon = abs(pdgId) == 13
    is_lepton = is_electron | is_muon

    mother_idx_valid = (mother_idx >= 0) & (mother_idx < ak.num(pdgId, axis=1))
    parent_pdg = ak.where(mother_idx_valid, pdgId[mother_idx], -9999)
    mother_is_top = parent_pdg == 6
    mother_is_antitop = parent_pdg == -6
    mother_is_Wplus = parent_pdg == 24
    mother_is_Wminus = parent_pdg == -24

    is_bottom_from_top = is_bottom & mother_is_top
    is_antibottom_from_antitop = is_antibottom & mother_is_antitop
    is_antilepton_from_top = ((pdgId == -11) | (pdgId == -13)) & mother_is_Wplus
    is_lepton_from_antitop = ((pdgId == 11) | (pdgId == 13)) & mother_is_Wminus

    has_top = ak.any(is_top, axis=1)
    has_antitop = ak.any(is_antitop, axis=1)
    has_l = ak.any(is_lepton_from_antitop, axis=1)
    has_lbar = ak.any(is_antilepton_from_top, axis=1)
    has_b = ak.any(is_bottom_from_top, axis=1)
    has_bbar = ak.any(is_antibottom_from_antitop, axis=1)

    dilepton_event_mask = has_top & has_antitop & has_l & has_lbar
    fully_valid = dilepton_event_mask & has_b & has_bbar

    return (
        genvec.E, genvec.px, genvec.py, genvec.pz,
        is_top, is_antitop, fully_valid,
        is_top, is_antitop,
        mother_is_Wplus, mother_is_Wminus,
        is_antilepton_from_top, is_lepton_from_antitop,
        mother_is_top, mother_is_antitop,
        is_bottom_from_top, is_antibottom_from_antitop
    )

def build_obs(arrays, outputs):
    valid_mask = outputs[-1]

    scattering_angle = np.asarray(outputs[0])
    ttbar_mass = np.asarray(outputs[1])
    B1 = np.asarray(outputs[2])
    B2 = np.asarray(outputs[3])
    C = np.asarray(outputs[4])
    ll_cHel = np.asarray(outputs[5])
    ls = outputs[6]
    lbars = outputs[7]
    bs = outputs[8]
    bbars = outputs[9]
    tops = outputs[10]
    tbars = outputs[11]

    gen_weights = np.asarray(arrays["Generator_weight"])
    weights = gen_weights[valid_mask]

    out = {
        "scattering_angle": scattering_angle,
        "ttbar_mass": ttbar_mass,
        "B1": B1,
        "B2": B2,
        "C": C,
        "ll_cHel": ll_cHel,
        "ls": ls,
        "lbars": lbars,
        "bs": bs,
        "bbars": bbars,
        "tops": tops,
        "tbars": tbars,
        "weights": weights,
        "cos_theta1k": B1[:, 0],
        "cos_theta1r": B1[:, 1],
        "cos_theta1n": B1[:, 2],
        "cos_theta2k": B2[:, 0],
        "cos_theta2r": B2[:, 1],
        "cos_theta2n": B2[:, 2],
        "l_pt": ls.pt,
        "lbar_pt": lbars.pt,
        "l_eta": ls.eta,
        "lbar_eta": lbars.eta,
        "l_phi": ls.phi,
        "lbar_phi": lbars.phi,
        "b_pt": bs.pt,
        "bbar_pt": bbars.pt,
        "b_eta": bs.eta,
        "bbar_eta": bbars.eta,
        "b_phi": bs.phi,
        "bbar_phi": bbars.phi,
        "dilepton_mass": (ls + lbars).mass
    }

    # Add composite C observables
    composite_C = compute_composite_C(C)
    for name, arr in composite_C.items():
        out[name] = np.asarray(arr)

    return out

    
# === File List (filtered) ===
def get_valid_files(directory, tree="Events"):
    files = glob.glob(f"{directory}/*.root")
    valid = []
    for f in files:
        try:
            with uproot.open(f) as rootfile:
                if tree in rootfile and rootfile[tree].num_entries > 0:
                    valid.append(f)
        except Exception as e:
            print(f"[SKIP] {f}: {e}")
    return valid

bins_config = {
    "angular": hist.axis.Regular(6, -1, 1, name="x"),
    "theta": hist.axis.Regular(20, -np.pi, 2 * np.pi, name="x"),
    "mass": hist.axis.Regular(40, 0, 2000, name="x"),
    "pt": hist.axis.Regular(30, 0, 300, name="x"),
    "eta": hist.axis.Regular(30, -3, 3, name="x"),
    "phi": hist.axis.Regular(30, -np.pi, np.pi, name="x")    
}

composite_labels = [
    (r"C_{kk}", "c_kk", "angular"),
    (r"C_{rr}", "c_rr", "angular"),
    (r"C_{nn}", "c_nn", "angular"),
    (r"C_{kn}", "c_kn", "angular"),
    (r"C_{rk}", "c_rk", "angular"),
    (r"C_{rn}", "c_rn", "angular"),
    (r"C_{kn}", "c_nk", "angular"),
    (r"C_{rk}", "c_kr", "angular"),
    (r"C_{rn}", "c_nr", "angular"),    
    (r"C_{nk}^{+}", "c_Pnk", "angular"),
    (r"C_{nk}^{-}", "c_Mnk", "angular"),
    (r"C_{rk}^{+}", "c_Prk", "angular"),
    (r"C_{rk}^{-}", "c_Mrk", "angular"),
    (r"C_{nr}^{+}", "c_Pnr", "angular"),
    (r"C_{nr}^{-}", "c_Mnr", "angular"),
    (r"C_{han}", "c_han", "angular"),
    (r"C_{sca}", "c_sca", "angular"),
    (r"C_{tra}", "c_tra", "angular"),
    (r"C_{kjL}", "c_kjL", "angular"),
    (r"C_{rqL}", "c_rqL", "angular"),
    (r"C_{rk}^{P}", "c_rkP", "angular"),
    (r"C_{rk}^{M}", "c_rkM", "angular"),
    (r"C_{nr}^{P}", "c_nrP", "angular"),
    (r"C_{nr}^{M}", "c_nrM", "angular"),
    (r"C_{nk}^{P}", "c_nkP", "angular"),
    (r"C_{nk}^{M}", "c_nkM", "angular"),
]

labels = [
    (r"cos(\phi_{l\bar{l}})", "ll_cHel", "angular"),
    (r"cos\theta^1_k", "cos_theta1k", "angular"),
    (r"cos\theta^1_r", "cos_theta1r", "angular"),
    (r"cos\theta^1_n", "cos_theta1n", "angular"),
    (r"cos\theta^2_k", "cos_theta2k", "angular"),
    (r"cos\theta^2_r", "cos_theta2r", "angular"),
    (r"cos\theta^2_n", "cos_theta2n", "angular"),
    (r"\theta^*_\text{scat} (rad)", "scattering_angle", "theta"),
    (r"M_{t\bar{t}}", "ttbar_mass", "mass"),
    (r"p_T\  (l^-)", "l_pt", "pt"),
    (r"p_T\  (l^+)", "lbar_pt", "pt"),
    (r"\eta\  (l^-)", "l_eta", "eta"),
    (r"\eta\  (l^+)", "lbar_eta", "eta"),
    (r"\phi\  (l^-)", "l_phi", "phi"),
    (r"\phi\  (l^+)", "lbar_phi", "phi"),
    (r"p_T\  (b)", "b_pt", "pt"),
    (r"p_T\  (\bar{b})", "bbar_pt", "pt"),
    (r"\eta\  (b)", "b_eta", "eta"),
    (r"\eta\  (\bar{b})", "bbar_eta", "eta"),
    (r"\phi\  (b)", "b_phi", "phi"),
    (r"\phi\  (\bar{b})", "bbar_phi", "phi"),
    (r"M_{l\bar{l}}", "dilepton_mass", "mass")    
]

def main(): 
    # --- Directories ---
    eft_dir = "/depot/cms/top/he614/EFT_FullRun2/nanogen_TT01j2lCARef_minimal_cut/"
    ref_dir = "/depot/cms/top/he614/notebooks/EFT_FullRun2/nanoaodv9_powhegv2_TTTo2L2Nu_SM_2016ULpreVFP/"
    outdir = "gen_spin_corr_plots_noEFT/minimal_cut/histograms/"
    os.makedirs(outdir, exist_ok=True)
    
    branches = [
        "GenPart_pt", "GenPart_eta", "GenPart_phi", "GenPart_mass",
        "GenPart_pdgId", "GenPart_status", "GenPart_genPartIdxMother",
        "Generator_weight"
    ]
    
    vector.register_awkward()
    
    # === Histograms ===
    h_ref_dict = {}
    h_eft_dict = {}
    
    for xlabel, key, bkey in labels + composite_labels:
        axis = bins_config[bkey]
        h_ref_dict[key] = hist.Hist(axis, storage=hist.storage.Weight())
        h_eft_dict[key] = hist.Hist(axis, storage=hist.storage.Weight())

    
    filename_refs = get_valid_files(ref_dir)
    filename_efts = get_valid_files(eft_dir)
    
    # === Streaming: SM reference ===
    for filename_ref in tqdm(filename_refs, desc="Streaming SM files"):
        try:
            with uproot.open(filename_ref) as fref:
                arrays_ref = fref["Events"].arrays(branches)
                inputs_ref = extract_inputs(arrays_ref)
                outputs_ref = compute_gen_spin_corrs(*inputs_ref)
                obs_ref = build_obs(arrays_ref, outputs_ref)
                for xlabel, key, bkey in labels + composite_labels:
                    if key not in obs_ref:
                        continue
                    h_ref_dict[key].fill(x=obs_ref[key], weight=obs_ref["weights"])
        except Exception as e:
            print(f"[ERROR] Failed to read {filename_ref}: {e}")
    
    # === Streaming: EFT files ===
    for filename_eft in tqdm(filename_efts, desc="Streaming EFT files"):
        try:
            with uproot.open(filename_eft) as feft:
                arrays_eft = feft["Events"].arrays(branches)
                inputs = extract_inputs(arrays_eft)
                outputs = compute_gen_spin_corrs(*inputs)
                obs = build_obs(arrays_eft, outputs)
                for xlabel, key, bkey in labels + composite_labels:
                    if key not in obs:
                        continue
                    h_eft_dict[key].fill(x=obs[key], weight=obs["weights"])
        except Exception as e:
            print(f"[ERROR] Failed to read {filename_eft}: {e}")

    save_histograms(h_ref_dict, h_eft_dict, outdir)
    
    # # === Plotting ===
    # for xlabel, key, bkey in labels + composite_labels:
    #     h = h_eft_dict.get(key)
    #     h_ref = h_ref_dict.get(key)
    
    #     if h is None or h_ref is None:
    #         print(f"[SKIP] Missing histograms for key: {key}")
    #         continue
    
    #     bins = bins_config[bkey]
    #     dx = np.diff(bins.edges)
    
    #     # Convert to uncertainties-aware arrays
    #     y_eft = unp.uarray(h.values(), np.sqrt(h.variances()))
    #     y_ref = unp.uarray(h_ref.values(), np.sqrt(h_ref.variances()))
    
    #     if unp.nominal_values(y_eft).sum() == 0 or unp.nominal_values(y_ref).sum() == 0:
    #         print(f"[SKIP] Empty histogram for key: {key}")
    #         continue
    
    #     # Normalize
    #     y_eft_norm = y_eft / (unp.nominal_values(y_eft).sum() * dx)
    #     y_ref_norm = y_ref / (unp.nominal_values(y_ref).sum() * dx)
    
    #     # Fill normalized histograms
    #     h_eft_norm = hist.Hist(bins, storage=hist.storage.Weight())
    #     h_ref_norm = hist.Hist(bins, storage=hist.storage.Weight())
    #     h_eft_norm.values()[...] = unp.nominal_values(y_eft_norm)
    #     h_ref_norm.values()[...] = unp.nominal_values(y_ref_norm)
    #     h_eft_norm.variances()[...] = unp.std_devs(y_eft_norm) ** 2
    #     h_ref_norm.variances()[...] = unp.std_devs(y_ref_norm) ** 2
    
    #     # Ratio and error
    #     ratio = unp.uarray(
    #         np.divide(unp.nominal_values(y_eft_norm), unp.nominal_values(y_ref_norm),
    #                   out=np.zeros_like(unp.nominal_values(y_ref_norm)),
    #                   where=unp.nominal_values(y_ref_norm) != 0),
    #         np.divide(unp.std_devs(y_eft_norm), unp.nominal_values(y_ref_norm),
    #                   out=np.zeros_like(unp.nominal_values(y_ref_norm)),
    #                   where=unp.nominal_values(y_ref_norm) != 0)
    #     )
    
    #     h_ratio = hist.Hist(bins, storage=hist.storage.Weight())
    #     h_ratio.values()[...] = unp.nominal_values(ratio)
    #     h_ratio.variances()[...] = unp.std_devs(ratio) ** 2
    
    #     # Plot
    #     fig, (ax_main, ax_ratio) = plt.subplots(
    #         2, 1, figsize=(5, 4), sharex=True,
    #         gridspec_kw={"height_ratios": [2, 1], "hspace": 0.1}
    #     )
    
    #     # Main plot
    #     mplhep.histplot(h_eft_norm, ax=ax_main, label="SMEFTsim_noEFT (NP=1)", histtype="step")
    #     mplhep.histplot(h_ref_norm, ax=ax_main, label="SM", histtype="step")
    #     ax_main.set_ylabel("Normalized Diff. Xsec", fontsize=12)
    #     ax_main.legend()
    #     ax_main.set_title("")
    
    #     # Ratio plot
    #     mplhep.histplot(h_ratio, ax=ax_ratio, histtype="step")
    #     ax_ratio.axhline(1.0, color="gray", linestyle="--")
    #     ax_ratio.set_ylabel(r"$\frac{\text{EFT}}{\text{SM}}$", fontsize=12)
    #     ax_ratio.set_xlabel(f"${xlabel}$")
    #     ax_ratio.set_ylim(0.95 * np.min(h_ratio.values()), 1.05 * np.max(h_ratio.values()))
    
    #     # Save
    #     fig.savefig(f"{outdir}/{key}.png", dpi=150, bbox_inches="tight")
    #     plt.close(fig)

if __name__ == "__main__":
    main()
