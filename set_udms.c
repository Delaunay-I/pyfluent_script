#include "udf.h"

#define C_U_dmd(c,t)    C_UDMI(c,t,udm_offset + 1)
#define C_GU_dmd(c,t)   C_UDMI(c,t,udm_offset + 2)
#define C_V_dmd(c,t)    C_UDMI(c,t,udm_offset + 3)
#define C_GV_dmd(c,t)   C_UDMI(c,t,udm_offset + 4)
#define C_W_dmd(c,t)    C_UDMI(c,t,udm_offset + 5)
#define C_GW_dmd(c,t)   C_UDMI(c,t,udm_offset + 6)

#define MAX(x, y) ((x > y) ? x:y)


#define _CRT_SECURE_NO_WARNINGS
// #define TURB

void calc_fluxes(const cell_t c, Thread* const t, const int n);

#define NUM_UDM 5

static int udm_offset = UDM_UNRESERVED;

DEFINE_EXECUTE_ON_LOADING(on_loading, libname)
{
    if (udm_offset == UDM_UNRESERVED)
        udm_offset =
            Reserve_User_Memory_Vars(NUM_UDM);

    if (udm_offset == UDM_UNRESERVED)
        Message0("\nYou need to define up to %d extra UDMs and "
                "then reload current library %s\n",
                NUM_UDM, libname);
    else
    {
        Message0("%d UDMs have been reserved by the current "
                "library %s\n",
                NUM_UDM, libname);

        Set_User_Memory_Name(udm_offset, "p_dmd");
        Set_User_Memory_Name(udm_offset + 1, "u_dmd");
        Set_User_Memory_Name(udm_offset + 2, "u_div");
        Set_User_Memory_Name(udm_offset + 3, "v_dmd");
        Set_User_Memory_Name(udm_offset + 4, "v_div");
        #ifdef TURB
        Set_User_Memory_Name(udm_offset + 5, "w_dmd");
        Set_User_Memory_Name(udm_offset + 6, "w_div");
        Set_User_Memory_Name(udm_offset + 7, "k_dmd");
        Set_User_Memory_Name(udm_offset + 8, "omega_dmd");
        #endif
    }
    Message0("\nUDM Offset for Current Loaded Library = %d", udm_offset);
}

DEFINE_ON_DEMAND(set_Field_udms)
{
    Domain *d = Get_Domain(1);
    Thread *t;
    cell_t c;

    // const char* filename = "./solver_data/DMDUpdate.csv";
    const char* filename = "./solver_data/solution_slim.csv";

    FILE* file = fopen(filename, "r");
    if (file == NULL){
        Message0("ERROR: cannot open the file %s. Abort UDF execution.\n", filename);
        perror("fopen");
        return 1;
    }

    if (udm_offset != UDM_UNRESERVED)
    {   
        thread_loop_c(t, d)
        {
            begin_c_loop(c, t)
            {
                real p=0, u=0, v=0;
                #if RP_2D
                fscanf(file, "%lf\t%lf\t%lf", &p, &u, &v);
                #endif
                #if RP_3D
                real w=0;
                fscanf (file, "%lf\t%lf\t%lf\t%lf", &p, &u, &v, &w);
                #endif

                C_UDMI(c, t, udm_offset) = p;
                C_UDMI(c, t, udm_offset + 1) = u;
                C_UDMI(c, t, udm_offset + 3) = v;
                #if RP_3D
                C_UDMI(c, t, udm_offset + 5) = w;
                #endif

                #ifdef TURB
                real k=0, omega=0;
                fscanf(file, "\t%lf\t%lf", &k, &omega);
                C_UDMI(c, t, udm_offset + 7) = k;
                C_UDMI(c, t, udm_offset + 8) = omega;
                #endif
                fscanf(file, "\n");

            }
            end_c_loop(c, t)
        }
        fclose(file);
        Message0("Vector fields recorded to UDMs from %s\n", filename);
    }
    else
        Message0("UDMs have not yet been reserved for library 1\n");
}

DEFINE_ON_DEMAND(calc_Grads)
{
    Domain *d = Get_Domain(1);
    Thread *t, *ft;
    cell_t c;
    face_t f;

    cell_t c0, c1 = -1;
    Thread *t0, *t1 = NULL;

    real NV_VEC(A);

    double tot_divergence = 0.0;
    double max_u = 0.0, max_v = 0.0;

if (udm_offset != UDM_UNRESERVED)
{
    /*
        * Calculating the gradients of the velocity components
        * and saving them to UDMs
        * Method: Calculating surface integrals for each cell
        */

    // Initializing the UDM gradients
    thread_loop_c(t, d)
    {
        begin_c_loop(c, t)
        {
            C_GU_dmd(c, t) = 0;
            C_GV_dmd(c, t) = 0;
            #if RP_3D
            C_GW_dmd(c, t) = 0;
            #endif
        }
        end_c_loop(c, t)
    }

// Calculating the gradients
thread_loop_f(ft, d)
{
    // BCs
    if (BOUNDARY_FACE_THREAD_P(ft))
    {
        begin_f_loop(f, ft)
        {
            c0 = F_C0(f, ft);
            t0 = F_C0_THREAD(f, ft);

            F_AREA(A, f, ft);

            // If the face value is available, use it
            if (NNULLP(THREAD_STORAGE(ft, SV_U))){
                max_u = MAX(max_u, F_U(f, ft));
                C_GU_dmd(c0, t0) += F_U(f, ft) * A[0];
            }                
            else {
                max_u = MAX(max_u, C_U_dmd(c0, t0));
                C_GU_dmd(c0, t0) += C_U_dmd(c0, t0) * A[0];
            }

            if (NNULLP(THREAD_STORAGE(ft, SV_V))){
                max_v = MAX(max_v, F_V(f, ft));
                C_GV_dmd(c0, t0) += F_V(f, ft) * A[1];
            }
            else {
                max_v = MAX(max_v, C_V_dmd(c0, t0));
                C_GV_dmd(c0, t0) += C_V_dmd(c0, t0) * A[1];
            }
        }
        end_f_loop(f, ft)
    }
    else
    {
        begin_f_loop(f, ft)
        {
            c0 = F_C0(f, ft);
            t0 = F_C0_THREAD(f, ft);
            c1 = F_C1(f, ft);
            t1 = F_C1_THREAD(f, ft);

            double d = 0.0;

            F_AREA(A, f, ft);
            
            // calculate face gradient
            double fGrad = (C_U_dmd(c1, t1) + C_U_dmd(c0, t0)) * .5 * A[0];
            C_GU_dmd(c0, t0) += fGrad;
            C_GU_dmd(c1, t1) -= fGrad;

            fGrad = (C_V_dmd(c1, t1) + C_V_dmd(c0, t0)) * .5 * A[1];
            C_GV_dmd(c0, t0) += fGrad;
            C_GV_dmd(c1, t1) -= fGrad;

            // Find max velocities
            max_u = MAX(max_u, C_U_dmd(c1, t1)); max_u = MAX(max_u, C_U_dmd(c0, t0));
            max_v = MAX(max_v, C_V_dmd(c1, t1)); max_v = MAX(max_v, C_V_dmd(c0, t0));
        }
        end_f_loop(f, ft)
    }
}

    // Normalize by Cell volume
    thread_loop_c(t, d)
    {
        begin_c_loop(c, t)
        {
            real cVol = C_VOLUME(c, t);
            C_GU_dmd(c, t) /= cVol;
            C_GV_dmd(c, t) /= cVol;
            #if RP_3D
            C_GW_dmd(c, t) /= cVol;
            #endif

            // calculate total divergence
            tot_divergence += C_GU_dmd(c, t) + C_GV_dmd(c, t);
            #if RP_3D
            tot_divergence += C_GW_dmd(c, t);
            #endif
        }
        end_c_loop(c, t)
    }

        const char* fname = "total_divergence.txt";

    FILE* file = fopen(fname, "w");
    if (file == NULL){
        Message0("ERROR: cannot open the file %s. Abort UDF execution.\n", fname);
        perror("fopen");
        return 1;
    }
    fprintf(file, "%.16Le\n", tot_divergence);
    fclose(file);

    Message0("DMD Gradients recorded in UDMs\n");
    Message0("Total divergence: %f\n", tot_divergence);
    double max_vel_mag = sqrt(max_u * max_u + max_v * max_v);
    Message0("Total divergence (normalized by max velocity magnitude): %f\n", tot_divergence/max_vel_mag);
}
else Message0("UDMs have not yet been reserved for library (set_udms.c)\n");

}