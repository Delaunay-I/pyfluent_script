#include <stdio.h>
#include <cassert>
#include <math.h>

#include "udf.h"
#define _CRT_SECURE_NO_WARNINGS
// #define TURB

DEFINE_ON_DEMAND(apply_man_update)
{
    Domain *d = Get_Domain(1);
    Thread *t;
    cell_t c;
    real pos[ND_ND];

    const char* filename = "solver_data/DMDUpdate.csv";

    FILE* file = fopen(filename, "r");
    if (file == NULL){
        Message("ERROR: cannot open the file %s. Abort UDF execution.\n", filename);
        perror("fopen");
        return 1;
    }

    thread_loop_c(t, d)
    {
        /* Loop over all cells in the current thread */
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
            #ifdef TURB
            real k=0, omega=0;
            fscanf(file, "\t%lf\t%lf", &k, &omega);
            #endif
            fscanf(file, "\n");

            C_CENTROID(pos, c, t);

            C_P(c, t) += p;
            C_U(c, t) += u;
            C_V(c, t) += v;
            #if RP_3D
            C_W(c, t) += w;
            #endif
            #ifdef TURB
            C_K(c, t) += k;
            C_O(c, t) += omega;
            #endif

        }
        end_c_loop(c, t)
    }
    fclose(file);
    Message0("solution file %s applied successfully\n", filename);

}