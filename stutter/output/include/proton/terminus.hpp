namespace proton {

class terminus {
  public:
    terminus() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}